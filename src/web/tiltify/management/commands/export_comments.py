from pathlib import Path

from django.core.management import BaseCommand

from src.web.tiltify.models import Campaign, Donation


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("id", type=int)

    def handle(self, *args, **options):
        campaign = Campaign.objects.get(id=options["id"])

        comments = list(
            Donation.objects.filter(campaign=campaign).exclude(comment=None).values_list("comment", flat=True)
        )
        Path("comments.txt").write_text("\n".join(comments))
