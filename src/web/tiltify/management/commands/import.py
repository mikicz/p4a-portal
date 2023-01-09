from django.core.management import BaseCommand

from src.client import schema
from src.client.api import get_campaign, get_rewards
from src.web.tiltify.models import Campaign, Reward


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
        print("Importing campaign details")
        c: schema.Campaign = get_campaign(campaign.id).data
        campaign.name = c.name
        campaign.slug = c.slug
        campaign.url = c.url
        campaign.description = c.description
        campaign.save()

    def import_polls(self, campaign: Campaign):
        print("Importing polls details")
        pass

    def import_rewards(self, campaign: Campaign):
        print("Importing rewards details")
        rewards = get_rewards(campaign.id).data
        reward: schema.Reward
        for reward in rewards:
            Reward.objects.update_or_create(
                id=reward.id,
                defaults={
                    "name": reward.name,
                    "amount": reward.amount,
                    "description": reward.description,
                    "kind": reward.kind,
                    "quantity": reward.quantity,
                    "remaining": reward.remaining,
                    "currency": reward.currency,
                    "active": reward.active,
                    "image_src": reward.image.src,
                    "image_alt": reward.image.alt,
                    "image_width": reward.image.width,
                    "image_height": reward.image.height,
                },
            )

    def import_donations(self, campaign: Campaign):
        print("Importing donations details")
        pass
