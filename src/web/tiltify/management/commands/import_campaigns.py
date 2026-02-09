from django.core.management import BaseCommand

from src.client.exceptions import CampaignNotFoundError
from src.web.tiltify.management.import_utils import import_campaign_details
from src.web.tiltify.models import Campaign


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.exclude(uuid=None).filter(keep_refreshing=True):
            try:
                import_campaign_details(campaign)
            except CampaignNotFoundError:
                self.stdout.write(f"Campaign {campaign.uuid} not found")
