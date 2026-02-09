from pathlib import Path

import git
import requests
from django.conf import settings
from django.core.management import BaseCommand
from django.urls import reverse
from django.utils import timezone

from src.web.tiltify.models import Campaign


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("id", type=int)
        parser.add_argument("path", type=str)

    def handle(self, *args, **options):
        campaign = Campaign.objects.get(id=options["id"])
        if not campaign.name:  # not imported yet
            print("Campaign has no name, skipping")
            return

        repo = git.Repo(options["path"])
        repo.remote().pull()

        url = reverse("campaign", args=[campaign.id])
        response = requests.get(settings.PROJECT_URL.rstrip("/") + url)

        (Path(options["path"]) / "index.html").write_bytes(response.content)

        repo.index.add("index.html")
        repo.index.commit(f"Update at {timezone.now().isoformat()}")
        repo.remote().push()
