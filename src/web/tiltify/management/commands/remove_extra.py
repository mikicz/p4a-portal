from django.core.management import BaseCommand

from src.client import schema
from src.web.tiltify.models import Campaign, Donation


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("id", type=int)
        parser.add_argument("--preview", action="store_true", default=False)

    def handle(self, *args, **options):
        campaign = Campaign.objects.get(id=options["id"])
        all_donations = schema.DonationList.parse_file("all_donations.json").donations
        all_donations_ids = {x.id for x in all_donations}
        donation_ids = set(
            Donation.objects.filter(
                campaign=campaign, completed_at__lte=max([x.completed_at for x in all_donations])
            ).values_list("uuid", flat=True)
        )

        print("In all donations", len(all_donations_ids))
        print("In database", len(donation_ids))
        print("Overlap", len(donation_ids & all_donations_ids))
        print("Missing in DB", len(all_donations_ids - donation_ids))
        print("Extra in DB", len(donation_ids - all_donations_ids))

        if not options["preview"]:
            for x in donation_ids - all_donations_ids:
                donation = Donation.objects.get(uuid=x)
                print(
                    donation.uuid,
                    donation.amount,
                    donation.name,
                    donation.comment,
                    donation.completed_at,
                    donation.reward,
                )
                donation.delete()
