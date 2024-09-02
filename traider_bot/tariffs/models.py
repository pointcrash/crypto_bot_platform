from django.contrib.auth.models import User
from django.db import models


class Tariff(models.Model):
    title = models.CharField(max_length=50)
    max_accounts = models.IntegerField()
    max_bots = models.IntegerField()
    max_income_per_month = models.IntegerField()
    response_time_from_support = models.CharField(max_length=50)


class UserTariff(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tariff = models.ForeignKey(Tariff, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)



