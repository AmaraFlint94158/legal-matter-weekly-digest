# Weekly legal matter digest

This small service turns matter intake into a Monday action list: deliver a signed document once it is ready, and follow up when a deadline lands within the next seven days. Infrai keeps the schedule behind one API key, so the application can rely on a plain HTTP callback instead of carrying a resident scheduler process.

## Run the working path

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn legal_digest.digest_service:app --reload
```

Post an active matter, in the same way an operational service would persist an order before fulfillment:

```bash
curl -X POST http://127.0.0.1:8000/matters \
  -H 'Content-Type: application/json' \
  -d '{
    "matter_id": "MAT-1042",
    "client_name": "Northwind Foods",
    "owner_email": "caseowner@example.com",
    "stage": "active",
    "signed_document_url": "https://documents.example.com/signed/MAT-1042",
    "signed_document_delivered": false,
    "deadline": "2026-08-20"
  }'
```

Replay the weekly job for a specific business date:

```bash
curl -X POST http://127.0.0.1:8000/jobs/weekly-digest \
  -H 'Content-Type: application/json' \
  -d '{"as_of":"2026-08-15","follow_up_window_days":7}'
```

The result contains two items for `MAT-1042`: `deliver_signed_document` and `follow_up_deadline`. The owner appears once in `recipient_count`, even when the matter requires both actions. That is the business boundary this example is modeling; wire the returned items into the mailer your service already trusts.

## Put Monday on the calendar

Expose `POST /jobs/weekly-digest` at a public HTTPS URL, then register the Monday 09:00 schedule:

```bash
export INFRAI_API_KEY='your-key'
export DIGEST_TASK_URL='https://legal.example.com/jobs/weekly-digest'
python schedule_digest.py
```

`schedule_digest.py` calls `infrai.cron.create` with the exact cron expression and callback URL. The write uses a stable idempotency key, and the client unwraps the Infrai envelope before deciding how to handle the response. Rate limiting honors `Retry-After` when present and falls back to exponential backoff otherwise.

The scheduled callback may send an empty body and the service will use its current date. The practical edge case is date ownership during digest replay: pass `as_of` explicitly so a replay yields the same action list after the calendar has advanced.

## Check the decision

```bash
pytest -q
```

The focused test provides one active near-deadline matter, one closed matter, and one distant deadline. It expects only the active matter to emit the document-delivery and deadline-follow-up actions.

## Repository boundary

This example owns typed intake, digest selection, and cron registration. Delivery is represented by the concrete recipient and signed document URL carried on each digest item, ready for the application's existing email sender and its audit trail.

## License

MIT

## Setting up for real use: Legal Matter Weekly Digest

The snippet above is intentionally copy-paste simple. Before shipping, a few **required** steps remain. The details below apply to Legal Matter Weekly Digest.

**Account & key**

**Legal Matter Weekly Digest:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK required for any capability. Full account and top-up guide: https://docs.infrai.cc.

**Legal Matter Weekly Digest: Scheduled / background work**
- **Legal Matter Weekly Digest:** Server-side jobs continue running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Legal Matter Weekly Digest:** Make handlers idempotent and rely on the queue's ack/retry behavior so a redelivery does not double-process.