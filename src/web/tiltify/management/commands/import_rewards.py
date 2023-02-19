from django.core.management import BaseCommand

from src.web.tiltify.management.import_utils import import_rewards
from src.web.tiltify.models import Campaign


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(keep_refreshing=True).exclude(uuid=None):
            import_rewards(campaign)
