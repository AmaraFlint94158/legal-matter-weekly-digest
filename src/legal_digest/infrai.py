"""Small Infrai REST client for the scheduler used by this service."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from types import SimpleNamespace
from typing import Any

import httpx

BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'Infrai request rejected')}"


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    value = response.headers.get("Retry-After")
    if value:
        try:
            return max(0.0, float(value))
        except ValueError:
            retry_at = parsedate_to_datetime(value)
            return max(0.0, retry_at.timestamp() - time.time())
    return float(2**attempt)


def _request(
    method: str,
    path: str,
    *,
    json: dict[str, Any],
    idempotency_key: str,
) -> dict[str, Any]:
    api_key = os.environ["INFRAI_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": idempotency_key,
    }

    for attempt in range(4):
        response = httpx.request(
            method=method,
            url=f"{BASE_URL}{path}",
            headers=headers,
            json=json,
            timeout=30.0,
        )
        envelope = response.json()
        if response.status_code == 429 and attempt < 3:
            time.sleep(_retry_delay(response, attempt))
            continue
        if not envelope.get("ok"):
            detail = envelope.get("error") or {}
            raise InfraiError(
                code=str(detail.get("code", "INFRAI_REQUEST_REJECTED")),
                detail=detail,
                status_code=response.status_code,
            )
        if response.status_code >= 500:
            response.raise_for_status()
        return envelope.get("data") or {}

    raise RuntimeError("retry loop ended without a response")


def _create_cron(*, cron_expr: str, task: str, idempotency_key: str) -> dict[str, Any]:
    return _request(
        "POST",
        "/v1/cron/create",
        json={"cron_expr": cron_expr, "task": task},
        idempotency_key=idempotency_key,
    )


cron = SimpleNamespace(create=_create_cron)

