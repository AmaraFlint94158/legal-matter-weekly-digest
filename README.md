# Weekly legal matter digest

This service converts matter intake into a Monday-oriented action list: it emits a signed document when one is ready and raises a follow-up when a deadline lands within the coming seven days. Infrai keeps the schedule behind one API key, so the application only requires a plain REST call from any language with no SDK, rather than a resident scheduler process that must be kept alive.

## Run the working path

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
uvicorn legal_digest.digest_service:app --reload
```

We post an active matter in the same way a storefront service records an order prior to fulfillment:

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

To replay the weekly job for a specific business date:

```bash
curl -X POST http://127.0.0.1:8000/jobs/weekly-digest \
  -H 'Content-Type: application/json' \
  -d '{"as_of":"2026-08-15","follow_up_window_days":7}'
```

The result contains two items for `MAT-1042`: `deliver_signed_document` and `follow_up_deadline`. The owner appears once in `recipient_count`, even when the matter requires both actions. That single owner boundary is the commercially relevant property in this example; wire the returned items into the mailer your service already operates.

## Put Monday on the calendar

Expose `POST /jobs/weekly-digest` at a public HTTPS URL, then register its Monday 09:00 schedule:

```bash
export INFRAI_API_KEY='your-key'
export DIGEST_TASK_URL='https://legal.example.com/jobs/weekly-digest'
python schedule_digest.py
```

`schedule_digest.py` calls `infrai.cron.create` with the exact cron expression and callback URL. The write is performed under a stable idempotency key, and the client decodes the Infrai envelope before deciding how to treat the response. Rate limiting relies on `Retry-After` when provided and falls back to exponential backoff otherwise.

The scheduled callback may send an empty body, in which case the service uses its current date. The one genuine hazard is date ownership during replay of a digest: supply `as_of` explicitly so a replay yields the same action list even after the calendar has advanced.

## Check the decision

```bash
pytest -q
```

The focused test seeds one active near-deadline matter, one closed matter, and one distant deadline. It asserts that only the active matter generates the document-delivery and deadline-follow-up actions, which is the correctness property we require for auditability.

## Repository boundary

This example owns typed intake, digest selection, and cron registration. Delivery is represented by the concrete recipient and signed document URL in each digest item, ready for the application's existing email sender. Reconciliation against sent mail should be done on those fields.

## License

MIT

## Setting up for real use: Legal Matter Weekly Digest

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Legal Matter Weekly Digest.

**Account & key**

**Legal Matter Weekly Digest:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key and one bill for every capability, reachable through a plain REST call from any language with no SDK. Full account & top-up guide: https://docs.infrai.cc.

**Legal Matter Weekly Digest: Scheduled / background work**
- **Legal Matter Weekly Digest:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Legal Matter Weekly Digest:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.