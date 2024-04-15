from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):
    ACCOUNT_TYPE_CHOICES = (
        ('CONTRACT', 'CONTRACT'),
        ('UNIFIED', 'UNIFIED'),
    )

    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(unique=True)
    service = models.ForeignKey('ExchangeService', on_delete=models.SET_NULL, null=True)
    API_TOKEN = models.CharField()
    SECRET_KEY = models.CharField()
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='CONTRACT', null=True)
    is_mainnet = models.BooleanField()
    url = models.CharField(default='https://api-testnet.bybit.com')

    def save(self, *args, **kwargs):
        if self.is_mainnet:
            self.url = 'https://api.bybit.com'
        else:
            self.url = 'https://api-testnet.bybit.com'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ActiveBot(models.Model):
    bot_id = models.CharField()


class ExchangeService(models.Model):
    name = models.CharField()

    def __str__(self):
        return self.name
