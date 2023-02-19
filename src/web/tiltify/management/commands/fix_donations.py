from collections import Counter

from django.core.management import BaseCommand

from src.client import schema
from src.web.tiltify.models import Campaign, Donation


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("id", type=int)
        parser.add_argument("--preview", action="store_true", default=False)

    def handle(self, *args, **options):
        # FIXME: make this run regularly?
        campaign = Campaign.objects.get(id=options["id"])
        all_donations = schema.DonationList.parse_file("all_donations.json").donations
        all_donations_ids = {x.id for x in all_donations}

        donation_ids_list = list(
            Donation.objects.filter(
                campaign=campaign, completed_at__lte=max([x.completed_at for x in all_donations])
            ).values_list("uuid", flat=True)
        )
        donation_ids_set = set(donation_ids_list)

        print("In all donations", len(all_donations_ids))
        print("In database", len(donation_ids_set))
        print("Overlap", len(donation_ids_set & all_donations_ids))
        print("Missing in DB", len(all_donations_ids - donation_ids_set))
        print("Extra in DB", len(donation_ids_set - all_donations_ids))

        duplicate_ids = {k for k, v in Counter(donation_ids_list).items() if v > 1}
        print("Duplicate", len(duplicate_ids))

        if not options["preview"]:
            for x in donation_ids_set - all_donations_ids:
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

            # FIXME: prevent this from happening entirely
            for x in duplicate_ids:
                donations = list(Donation.objects.filter(uuid=x))
                for y in donations[1:]:
                    y.delete()
