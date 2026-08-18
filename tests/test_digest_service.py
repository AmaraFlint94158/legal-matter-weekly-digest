from datetime import date

from legal_digest.digest_service import DigestRequest, MatterIntake, build_digest


def test_digest_selects_delivery_and_near_deadline_actions() -> None:
    matters = [
        MatterIntake(
            matter_id="MAT-1042",
            client_name="Northwind Foods",
            owner_email="caseowner@example.com",
            stage="active",
            signed_document_url="https://documents.example.com/signed/MAT-1042",
            signed_document_delivered=False,
            deadline=date(2026, 8, 20),
        ),
        MatterIntake(
            matter_id="MAT-1043",
            client_name="Tailspin Toys",
            owner_email="caseowner@example.com",
            stage="closed",
            deadline=date(2026, 8, 18),
        ),
        MatterIntake(
            matter_id="MAT-1044",
            client_name="Contoso Retail",
            owner_email="counsel@example.com",
            stage="active",
            deadline=date(2026, 9, 30),
        ),
    ]

    result = build_digest(
        matters,
        DigestRequest(as_of=date(2026, 8, 15), follow_up_window_days=7),
    )

    assert result.recipient_count == 1
    assert [item.action for item in result.items] == [
        "deliver_signed_document",
        "follow_up_deadline",
    ]
    assert {item.matter_id for item in result.items} == {"MAT-1042"}

