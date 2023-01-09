from django.core.management import BaseCommand

from src.client.api import get_campaign
from src.web.tiltify.models import Campaign


class Command(BaseCommand):
    def handle(self, *args, **options):
        for campaign in Campaign.objects.all():
            self.import_campaign(campaign)

    def import_campaign(self, campaign: Campaign):
        self.import_campaign_details(campaign)
        self.import_polls(campaign)
        self.import_rewards(campaign)
        self.import_donations(campaign)

    def import_campaign_details(self, campaign: Campaign):
        c = get_campaign(campaign.id).data
        campaign.name = c.name
        campaign.slug = c.slug
        campaign.url = c.url
        campaign.description = c.description
        campaign.save()

    def import_polls(self, campaign: Campaign):
        pass

    def import_rewards(self, campaign: Campaign):
        pass

    def import_donations(self, campaign: Campaign):
        pass


