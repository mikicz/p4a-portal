from django.core.management import BaseCommand

from src.client.exceptions import CampaignNotFoundError
from src.web.tiltify.management.import_utils import import_campaign_details, import_rewards
from src.web.tiltify.models import Campaign


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.filter(keep_refreshing=True).exclude(uuid=None):
            try:
                if not campaign.name:
                    import_campaign_details(campaign)
            except CampaignNotFoundError:
                print(f"Campaign {campaign.uuid} not found")
                continue
            import_rewards(campaign)
