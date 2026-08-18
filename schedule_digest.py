"""Register the weekly digest callback with Infrai."""

import os

from legal_digest import infrai


def register_weekly_digest() -> str:
    task_url = os.environ["DIGEST_TASK_URL"]
    result = infrai.cron.create(
        cron_expr="0 9 * * 1",
        task=task_url,
        idempotency_key="legal-weekly-digest-v1",
    )
    return str(result["job_id"])


if __name__ == "__main__":
    print(f"Scheduled weekly legal digest: {register_weekly_digest()}")

