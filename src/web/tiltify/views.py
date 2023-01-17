import json
from collections import Counter
from datetime import datetime, tzinfo, UTC

import pandas as pd
from django.db import models
from django.db.models import Count, Sum, ExpressionWrapper, Q
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
        data["anonymous_statistics"] = json.dumps(self.get_anonymous_statistics(), indent=2)
        data["decimal_statistics"] = json.dumps(self.get_decimal_statistics(), indent=2)
        war, war_stream = self.get_decimal_war_statistics()
        data["decimal_war_statistics"] = json.dumps(war, indent=2)
        data["decimal_war_stream_statistics"] = json.dumps(war_stream, indent=2)

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

    def get_anonymous_statistics(self):
        df = pd.DataFrame.from_records(
            Donation.objects.filter(campaign=self.object)
            .annotate(is_anonymous=ExpressionWrapper(Q(name="Anonymous"), output_field=models.BooleanField()))
            .values("is_anonymous")
            .annotate(count=Count("id"), total=Sum("amount"))
        ).astype({"total": float})
        df["who"] = df["is_anonymous"].map(lambda x: "Anonymous" if x else "Other")
        df.drop(columns={"is_anonymous"}, inplace=True)

        return df.to_dict("records")

    def get_decimal_statistics(self):
        df = pd.DataFrame.from_records(Donation.objects.filter(campaign=self.object).values("amount"))

        df["after_decimal"] = df["amount"].map(lambda x: x % 1)

        df = df.groupby(["after_decimal"]).count().reset_index().astype({"after_decimal": "string"})
        df["after_decimal"] = df["after_decimal"].str.split(".", expand=True)[1]
        df.sort_values(by=["amount"], inplace=True, ascending=False)

        return df.to_dict("records")

    def get_decimal_counter(self, df):

        start = df.iloc[0].time
        current_value = None

        counter = Counter()

        for row in df.itertuples():
            if row.after_decimal != current_value:
                if current_value is not None:
                    counter[current_value] += (row.time - start).total_seconds() / 60

                current_value = row.after_decimal
                start = row.time

        counter_df = pd.DataFrame(list(counter.items()), columns=["after_decimal", "minutes"]).sort_values(
            "minutes", ascending=False
        )
        counter_df["minutes"] = counter_df["minutes"].round(2)
        counter_df["percentage_of_total"] = counter_df["minutes"] / counter_df["minutes"].sum() * 100

        return counter_df[:10].reset_index(drop=True)

    def get_decimal_war_statistics(self):
        df = pd.DataFrame.from_records(Donation.objects.filter(campaign=self.object).values("amount", "completed_at"))
        df["time"] = df["completed_at"]
        df["amount_in_pennies"] = (df["amount"] * 100).astype(int)
        df.sort_values(by=["time"], inplace=True)
        df["tiltify_total"] = df["amount_in_pennies"].cumsum()
        df["after_decimal"] = (df["tiltify_total"] % 100).map(lambda x: "{:02d}".format(x))

        df = df[["after_decimal", "time"]]
        decimal_all = self.get_decimal_counter(df)
        # TODO: fix hardcoded
        decimal_stream = self.get_decimal_counter(
            df[
                (df["time"] >= pd.to_datetime(datetime(2022, 2, 25, 17, 0, 0, tzinfo=UTC)))
                & (df["time"] <= pd.to_datetime(datetime(2022, 2, 27, 17, 0, 0, tzinfo=UTC)))
            ]
        )
        return decimal_all.to_dict("records"), decimal_stream.to_dict("records")