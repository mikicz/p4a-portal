import json

import pandas as pd
from django.db.models import Count, Sum
from django.views.generic import ListView, DetailView
from .models import Campaign, Donation, Reward


class CampaignsView(ListView):
    model = Campaign
    template_name = "campaigns.html"


class CampaignView(DetailView):
    model = Campaign
    template_name = "campaign.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["reward_statistics"] = json.dumps(self.get_reward_statistics(), indent=2)

        return data

    def get_reward_statistics(self):
        df = pd.DataFrame.from_records(
            Donation.objects.filter(campaign=self.object)
            .values("reward_id")
            .annotate(count=Count("id"), total=Sum("amount"))
        ).astype({"total": float})
        rewards = {x.id: x for x in Reward.objects.all()}
        df["name"] = df["reward_id"].map(lambda x: rewards[x].name if not pd.isna(x) else None)
        df["base_price"] = df["reward_id"].map(lambda x: rewards[x].amount if not pd.isna(x) else None).astype(float)
        df["raised_over_base"] = df["total"] - (df["count"] * df["base_price"])
        total = df["total"].sum()
        df["percentage_of_total"] = (df["total"] / total) * 100
        df["average"] = df["total"] / df["count"]
        df.sort_values(by=["total"], inplace=True, ascending=False)
        df.drop(columns={"reward_id"}, inplace=True)

        return df.to_dict("records")
