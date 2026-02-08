from django.tasks import task

from src.client.schema import DonationWebhook


@task
def process_webhook_task(*, data: str) -> None:
    webhook = DonationWebhook.parse_raw(data)

    print(webhook)

    return {
        "campaign_id": webhook.data.campaign_id,
        "donation_id": webhook.data.id,
    }
