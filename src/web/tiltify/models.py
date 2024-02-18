from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils.functional import cached_property


class Campaign(models.Model):
    id = models.IntegerField(primary_key=True)
    uuid = models.UUIDField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.CharField(max_length=255, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    supportable = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    stream_start = models.DateTimeField(null=True, blank=True)
    stream_end = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    stats_refresh_finished = models.DateTimeField(null=True, blank=True)
    polls_refresh_finished = models.DateTimeField(null=True, blank=True)
    keep_refreshing = models.BooleanField(default=True)

    def __str__(self):
        return f"Campaign<{self.id}, {self.name}>"


class Reward(models.Model):
    uuid = models.UUIDField(null=True, blank=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True)
    amount = models.DecimalField(decimal_places=2, max_digits=20, null=True)
    description = models.TextField(null=True)
    kind = models.CharField(max_length=255, null=True)
    quantity = models.IntegerField(null=True)
    remaining = models.IntegerField(null=True)
    currency = models.CharField(max_length=255, null=True)
    active = models.BooleanField(null=True)
    image_src = models.CharField(max_length=255, null=True)
    image_alt = models.CharField(max_length=255, null=True)
    image_width = models.IntegerField(null=True)
    image_height = models.IntegerField(null=True)
    missing = models.BooleanField(default=False)

    inserted_at = models.DateTimeField(default=None, null=True, blank=True)
    starts_at = models.DateTimeField(default=None, null=True, blank=True)
    ends_at = models.DateTimeField(default=None, null=True, blank=True)
    updated_at = models.DateTimeField(default=None, null=True, blank=True)

    def has_image(self):
        return self.image_src != "https://assets.tiltify.com/assets/default-reward.png"

    def __str__(self):
        return self.name or self.uuid


class Poll(models.Model):
    id = models.UUIDField(primary_key=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    test_poll = models.BooleanField(default=False)

    @cached_property
    def total(self) -> Decimal:
        return sum(x.total_amount_raised for x in self.option_set.all())

    @cached_property
    def winning(self) -> Option | None:
        max_amount = max(x.total_amount_raised for x in self.option_set.all())
        for option in self.option_set.all():
            if option.total_amount_raised == max_amount:
                return option
        return None


class Option(models.Model):
    id = models.UUIDField(primary_key=True)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    total_amount_raised = models.DecimalField(decimal_places=2, max_digits=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()


class Donation(models.Model):
    id = models.UUIDField(primary_key=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=20)
    name = models.CharField(max_length=255)
    comment = models.TextField(null=True, blank=True)
    completed_at = models.DateTimeField()


class RewardClaim(models.Model):
    id = models.UUIDField(primary_key=True)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE)
