"""Matter intake and the weekly legal operations digest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from threading import Lock
from typing import Literal

@dataclass
class MatterIntake:
    matter_id: str
    client_name: str
    owner_email: str
    stage: Literal["intake", "active", "closed"]
    signed_document_url: str | None = None
    signed_document_delivered: bool = False
    deadline: date | None = None

    def __post_init__(self) -> None:
        if not self.matter_id or not self.client_name or len(self.owner_email) < 3:
            raise ValueError("matter_id, client_name, and owner_email are required")
        if self.stage not in {"intake", "active", "closed"}:
            raise ValueError(f"invalid matter stage: {self.stage}")


@dataclass
class DigestRequest:
    as_of: date
    follow_up_window_days: int = 7

    def __post_init__(self) -> None:
        if not 1 <= self.follow_up_window_days <= 30:
            raise ValueError("follow_up_window_days must be between 1 and 30")


@dataclass
class DigestItem:
    matter_id: str
    client_name: str
    owner_email: str
    action: Literal["deliver_signed_document", "follow_up_deadline"]
    due_on: date | None = None
    signed_document_url: str | None = None


@dataclass
class DigestResult:
    subject: str
    items: list[DigestItem]
    recipient_count: int


class MatterBook:
    def __init__(self) -> None:
        self._matters: dict[str, MatterIntake] = {}
        self._lock = Lock()

    def record(self, matter: MatterIntake) -> MatterIntake:
        with self._lock:
            self._matters[matter.matter_id] = matter
        return matter

    def snapshot(self) -> list[MatterIntake]:
        with self._lock:
            return list(self._matters.values())


def build_digest(matters: list[MatterIntake], request: DigestRequest) -> DigestResult:
    items: list[DigestItem] = []
    for matter in matters:
        if matter.stage == "closed":
            continue
        if matter.signed_document_url and not matter.signed_document_delivered:
            items.append(
                DigestItem(
                    matter_id=matter.matter_id,
                    client_name=matter.client_name,
                    owner_email=matter.owner_email,
                    action="deliver_signed_document",
                    signed_document_url=matter.signed_document_url,
                )
            )
        if matter.deadline is not None:
            days_left = (matter.deadline - request.as_of).days
            if 0 <= days_left <= request.follow_up_window_days:
                items.append(
                    DigestItem(
                        matter_id=matter.matter_id,
                        client_name=matter.client_name,
                        owner_email=matter.owner_email,
                        action="follow_up_deadline",
                        due_on=matter.deadline,
                    )
                )

    recipients = {item.owner_email for item in items}
    return DigestResult(
        subject=f"Legal operations digest for {request.as_of.isoformat()}",
        items=items,
        recipient_count=len(recipients),
    )


matter_book = MatterBook()

def intake_matter(matter: MatterIntake) -> MatterIntake:
    return matter_book.record(matter)


def weekly_digest(request: DigestRequest | None = None) -> DigestResult:
    digest_request = request or DigestRequest(as_of=date.today())
    return build_digest(matter_book.snapshot(), digest_request)


try:
    from fastapi import FastAPI
except ModuleNotFoundError:  # The digest domain can run without the HTTP adapter.
    app = None
else:
    app = FastAPI(title="Legal digest service")
    app.post("/matters", response_model=MatterIntake)(intake_matter)
    app.post("/jobs/weekly-digest", response_model=DigestResult)(weekly_digest)
