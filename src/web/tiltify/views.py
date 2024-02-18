import datetime
import json
from collections import Counter

import pandas as pd
from django.db import models
from django.db.models import Count, ExpressionWrapper, Max, Min, Q, Sum
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Campaign, Donation, Poll, Reward, RewardClaim


class CampaignsView(ListView):
    model = Campaign
    template_name = "campaigns.html"


class CampaignView(DetailView):
    model = Campaign
    template_name = "campaign.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["reward_statistics"] = json.dumps(self.get_reward_statistics(), indent=2)
        data["donation_statistics"] = json.dumps(self.get_donation_statistics(), indent=2)
        data["reward_combinations"] = json.dumps(self.get_reward_combinations(), indent=2)
        data["anonymous_statistics"] = json.dumps(self.get_anonymous_statistics(), indent=2)
        data["decimal_statistics"] = json.dumps(self.get_decimal_statistics(), indent=2)
        war, war_stream = self.get_decimal_war_statistics()
        data["decimal_war_statistics"] = json.dumps(war, indent=2)
        data["decimal_war_stream_statistics"] = json.dumps(war_stream, indent=2)

        data["polls"] = (
            Poll.objects.filter(campaign=self.object)
            .prefetch_related("option_set")
            .order_by("created_at")
            .exclude(test_poll=True)
        )
        data["rewards"] = (
            Reward.objects.filter(campaign=self.object)
            .exclude(missing=True)
            .order_by("-active", "amount", "name", "id")
        )

        data["now"] = timezone.now()
        data["total"] = Donation.objects.filter(campaign=self.object).aggregate(amount=Sum("amount"))["amount"]

        return data

    def get_reward_name(self, reward_id, rewards):
        if pd.isna(reward_id):
            return None

        if rewards[reward_id].missing:
            return "(???? missing from API)"

        return rewards[reward_id].name

    def get_reward_base_price(self, reward_id, rewards):
        if pd.isna(reward_id) or rewards[reward_id].missing:
            return None

        return rewards[reward_id].amount

    def get_donation_statistics(self):
        df = pd.DataFrame.from_records(
            Donation.objects.filter(campaign=self.object)
            .annotate(rewards=Count("rewardclaim"))
            .values("id", "rewards", "amount")
        )
        if df.empty:
            return []
        df = df.groupby(by=["rewards"]).agg(total=("amount", "sum"), count=("id", "count")).reset_index()
        df["total"] = df["total"].astype(float)
        df.sort_values(by=["count", "rewards"], inplace=True, ascending=False)
        return df.to_dict("records")

    def get_reward_combinations(self):
        df = pd.DataFrame.from_records(
            RewardClaim.objects.filter(donation__campaign=self.object).values("donation_id", "reward_id")
        )

        if df.empty:
            return []

        grouped_donations = df.groupby("donation_id")["reward_id"].apply(frozenset).reset_index()
        grouped_donations = grouped_donations[grouped_donations["reward_id"].map(len) > 1]
        if grouped_donations.empty:
            return []

        combinations = (
            grouped_donations.groupby(["reward_id"])
            .count()
            .reset_index()
            .rename(columns={"donation_id": "count"})
            .sort_values("count", ascending=False)
        )
        rewards = dict(Reward.objects.filter(campaign=self.object).values_list("id", "name"))

        def get_names(reward_ids):
            return ", ".join(sorted([rewards[x] or "(???? missing from API)" for x in reward_ids]))

        combinations["reward_names"] = combinations["reward_id"].map(get_names)

        return combinations.drop(columns=["reward_id"]).to_dict("records")

    def get_reward_statistics(self):
        no_reward_stats = (
            Donation.objects.filter(campaign=self.object)
            .filter(rewardclaim__isnull=True)
            .aggregate(count=Count("id"), total=Sum("amount"))
        )
        df = pd.DataFrame.from_records(
            RewardClaim.objects.filter(donation__campaign=self.object)
            .values("reward_id")
            .annotate(count=Sum("quantity"))
        )
        if df.empty:
            return []

        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    [
                        {
                            "reward_id": None,
                            "count": no_reward_stats["count"],
                            "total": no_reward_stats["total"],
                        }
                    ]
                ),
            ]
        )

        df = df.astype({"total": float})
        rewards = {x.id: x for x in Reward.objects.all()}

        reward_start = {}
        reward_end = {}
        for reward_id, reward in rewards.items():
            if reward.active:
                continue

            reward_start[reward_id] = reward.starts_at
            if reward_start[reward_id] is None:
                reward_start[reward_id] = Donation.objects.filter(rewardclaim__reward=reward).aggregate(
                    min=Min("completed_at")
                )["min"]
            reward_end[reward_id] = Donation.objects.filter(rewardclaim__reward=reward).aggregate(
                max=Max("completed_at")
            )["max"]

        def sold_out_in(reward_id_) -> str | None:
            if reward_id_ not in reward_start:
                return None
            seconds = (reward_end[reward_id_] - reward_start[reward_id_]).total_seconds()
            return str(datetime.timedelta(seconds=round(seconds)))

        df["name"] = df["reward_id"].map(lambda x: self.get_reward_name(x, rewards))
        df["base_price"] = df["reward_id"].map(lambda x: self.get_reward_base_price(x, rewards)).astype(float)
        df["total"] = df["total"].fillna(df["base_price"] * df["count"])
        total = df["total"].sum()
        df["percentage_of_total"] = (df["total"] / total) * 100

        df["sold_out_in"] = df["reward_id"].map(sold_out_in)

        df.sort_values(by=["total", "count", "reward_id"], inplace=True, ascending=False)
        df.drop(columns={"reward_id"}, inplace=True)

        return df.to_dict("records")

    def get_anonymous_statistics(self):
        df = pd.DataFrame.from_records(
            Donation.objects.filter(campaign=self.object)
            .annotate(is_anonymous=ExpressionWrapper(Q(name="Anonymous"), output_field=models.BooleanField()))
            .values("is_anonymous")
            .annotate(count=Count("id"), total=Sum("amount"))
        )
        if df.empty:
            return []
        df = df.astype({"total": float})
        df["who"] = df["is_anonymous"].map(lambda x: "Anonymous" if x else "Other")
        df.drop(columns={"is_anonymous"}, inplace=True)

        return df.to_dict("records")

    def get_decimal_statistics(self):
        df = pd.DataFrame.from_records(Donation.objects.filter(campaign=self.object).values("amount"))
        if df.empty:
            return []

        df["after_decimal"] = df["amount"].map(lambda x: x % 1)

        df = df.groupby(["after_decimal"]).count().reset_index().astype({"after_decimal": "string"})
        df["after_decimal"] = df["after_decimal"].str.split(".", expand=True)[1]
        df.sort_values(by=["amount"], inplace=True, ascending=False)

        return df.to_dict("records")

    def get_decimal_counter(self, df):
        start = df.iloc[0].time
        current_value = None

        counter = Counter()

        row = None
        for row in df.itertuples():
            if row.after_decimal != current_value:
                if current_value is not None:
                    counter[current_value] += (row.time - start).total_seconds() / 60

                current_value = row.after_decimal
                start = row.time

        # add the last value
        if row is not None and current_value is not None:
            counter[current_value] += (row.time - start).total_seconds() / 60

        counter_df = pd.DataFrame(list(counter.items()), columns=["after_decimal", "minutes"]).sort_values(
            "minutes", ascending=False
        )
        counter_df["minutes"] = counter_df["minutes"].round(2)
        counter_df["percentage_of_total"] = counter_df["minutes"] / counter_df["minutes"].sum() * 100

        return counter_df[:10].reset_index(drop=True)

    def get_decimal_war_statistics(self):
        qs = Donation.objects.filter(campaign=self.object)
        if self.object.retired_at is not None:
            qs = qs.filter(completed_at__lte=self.object.retired_at)
        df = pd.DataFrame.from_records(qs.values("amount", "completed_at"))
        if df.empty:
            return [], []
        df["time"] = df["completed_at"]
        df["amount_in_pennies"] = (df["amount"] * 100).astype(int)
        df.sort_values(by=["time"], inplace=True)
        df["tiltify_total"] = df["amount_in_pennies"].cumsum()
        df["after_decimal"] = (df["tiltify_total"] % 100).map(lambda x: f"{x:02d}")

        df = df[["after_decimal", "time"]]
        decimal_all = self.get_decimal_counter(df)
        if self.object.stream_start is None:
            start, end = df["time"].min(), df["time"].max()
        else:
            start, end = self.object.stream_start, self.object.stream_end

        df_stream = df[(df["time"] >= pd.to_datetime(start)) & (df["time"] <= pd.to_datetime(end))]
        if df_stream.empty:
            decimal_stream = []
        else:
            decimal_stream = self.get_decimal_counter(
                df[(df["time"] >= pd.to_datetime(start)) & (df["time"] <= pd.to_datetime(end))]
            ).to_dict("records")
        return decimal_all.to_dict("records"), decimal_stream
