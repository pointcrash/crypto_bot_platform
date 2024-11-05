from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Tariff(models.Model):
    TARIFF_TYPE_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
        ('ARCHIVED', 'ARCHIVED'),
        ('ADMIN', 'ADMIN'),
    )

    title = models.CharField(max_length=50)
    max_accounts = models.IntegerField()
    max_bots = models.IntegerField()
    max_income_per_month = models.IntegerField()
    response_time_from_support = models.IntegerField(default=7)
    price = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    type = models.CharField(max_length=25, choices=TARIFF_TYPE_CHOICES, default='INACTIVE', null=True)
    duration = models.DurationField(default=timedelta(days=30), null=True)

    def __str__(self):
        return self.title


class UserTariff(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_time = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        created_date = self.created_at or timezone.now()

        if not self.expiration_time:
            if self.tariff and self.tariff.duration:
                self.expiration_time = created_date + self.tariff.duration
            else:
                self.expiration_time = created_date + timedelta(days=30)

        super().save(*args, **kwargs)
