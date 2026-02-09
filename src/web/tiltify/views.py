import datetime
import json
from collections import Counter
from decimal import Decimal
from uuid import UUID

import pandas as pd
from django.db import models
from django.db.models import Count, ExpressionWrapper, Max, Min, Q, Sum
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, ListView
from django.views.generic.base import View

from .models import Campaign, Donation, Option, Reward, RewardClaim
from .tasks import process_webhook_task


class CampaignsView(ListView):
    queryset = Campaign.objects.exclude(name__isnull=True).exclude(name="")
    template_name = "campaigns.html"


class CampaignView(DetailView):
    queryset = Campaign.objects.exclude(name__isnull=True).exclude(name="")
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
        data["donation_breakdown"] = json.dumps(self.get_donation_breakdown(), indent=2)

        data["polls_v2"] = self.get_polls()
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

    def get_polls(self):
        donations = pd.DataFrame(
            Donation.objects.filter(poll_option_id__isnull=False, campaign=self.object)
            .annotate(reward_count=Count("rewardclaim"))
            .values("poll_option_id", "reward_count")
        )
        if donations.empty:
            return None
        donations["has_reward"] = donations["reward_count"] > 0

        donations_to_polls_df_indexed = donations.groupby(["poll_option_id", "has_reward"]).count()
        donations_to_polls_df = donations_to_polls_df_indexed.reset_index()
        donations_to_polls_dict: dict[tuple[UUID, bool], int] = {}
        for poll_option_id in donations_to_polls_df.reset_index()["poll_option_id"].unique():
            try:
                donations_to_polls_dict[(poll_option_id, True)] = donations_to_polls_df_indexed.loc[
                    (poll_option_id, True)
                ]["reward_count"]
            except KeyError:
                donations_to_polls_dict[(poll_option_id, True)] = 0
            try:
                donations_to_polls_dict[(poll_option_id, False)] = donations_to_polls_df_indexed.loc[
                    (poll_option_id, False)
                ]["reward_count"]
            except KeyError:
                donations_to_polls_dict[(poll_option_id, False)] = 0

        options = pd.DataFrame.from_records(
            Option.objects.filter(poll__test_poll=False, poll__campaign=self.object)
            .values(
                "id",
                "name",
                "total_amount_raised",
                "created_at",
                "updated_at",
                "poll__id",
                "poll__name",
                "poll__active",
                "poll__created_at",
                "poll__updated_at",
            )
            .order_by("poll__created_at", "created_at")
        )
        options["votes"] = options["id"].map(
            lambda x: donations_to_polls_dict.get((x, True), 0) + donations_to_polls_dict.get((x, False), 0)
        )
        options["votes_with_reward"] = options["id"].map(lambda x: donations_to_polls_dict.get((x, True), 0))
        options["votes_without_reward"] = options["id"].map(lambda x: donations_to_polls_dict.get((x, False), 0))
        winning_options_amount = {}
        winning_options_id = {}
        for row in options.itertuples():
            winning_options_id.setdefault(row.poll__id, row.id)
            winning_options_amount.setdefault(row.poll__id, row.total_amount_raised)

            if row.total_amount_raised > winning_options_amount[row.poll__id]:
                winning_options_id[row.poll__id] = row.id
                winning_options_amount[row.poll__id] = row.total_amount_raised

        winning_options_ids = set(winning_options_id.values())

        options["winning"] = options["id"].map(lambda x: x in winning_options_ids)

        final_data = {}
        for row in options.itertuples():  # type: Any
            final_data.setdefault(
                row.poll__id,
                {
                    "poll_id": row.poll__id,
                    "poll_name": row.poll__name,
                    "poll_active": row.poll__active,
                    "poll_created_at": row.poll__created_at,
                    "poll_updated_at": row.poll__updated_at,
                    "total": Decimal(0),
                    "options": [],
                },
            )
            final_data[row.poll__id]["options"].append(row)
            final_data[row.poll__id]["total"] += row.total_amount_raised

        return list(final_data.values())

    def get_donation_breakdown(self):
        donations = pd.DataFrame.from_records(Donation.objects.filter(campaign=self.object).values("amount")).astype(
            {"amount": float}
        )
        if donations.empty:
            return None

        values = []

        max_value = donations["amount"].max()
        i = 0
        while i < max_value:
            count = len(donations[(donations["amount"] >= i) & (donations["amount"] < i + 10)])
            if count:
                values.append((i, i + 10, count))
            i += 10

        return values


class WebhookView(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse("OK")

    def post(self, request: HttpRequest, *args, **kwargs):
        task_result = process_webhook_task.enqueue(request.body.decode("utf-8"))

        return HttpResponse(task_result.id)
