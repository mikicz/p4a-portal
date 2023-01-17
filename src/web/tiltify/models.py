from django.db import models


class Campaign(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.CharField(max_length=255, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Campaign<{self.id}, {self.name}>"


class Reward(models.Model):
    # TODO: add campaign
    name = models.CharField(max_length=255)
    amount = models.DecimalField(decimal_places=2, max_digits=20)
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
    comment = models.TextField(null=True, blank=True)
    completed_at = models.DateTimeField()
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, null=True, blank=True)
