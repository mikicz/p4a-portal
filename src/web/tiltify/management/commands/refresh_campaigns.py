from django.core.management import BaseCommand

from src.web.tiltify.management.import_utils import import_campaign_details
from src.web.tiltify.models import Campaign


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.exclude(uuid=None):
            import_campaign_details(campaign)
