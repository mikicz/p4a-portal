from django.tasks import task


@task
def process_webhook_task(webhook_body: str) -> None:
    pass
