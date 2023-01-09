from django.db import models


class Campaign(models.Model):
    pass


class Reward(models.Model):
    name = models.CharField(max_length=255)
    amount = models.DecimalField(decimal_places=2, max_digits=20)


class Poll(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()


class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    total_amount_raised = models.DecimalField(decimal_places=2, max_digits=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()


class Donation(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    amount = models.DecimalField(decimal_places=2, max_digits=20)
    name = models.CharField(max_length=255)
    comment = models.CharField(max_length=255, null=True, blank=True)
    completed_at = models.DateTimeField()
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, null=True, blank=True)
