from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField()
    API_TOKEN = models.CharField()
    SECRET_KEY = models.CharField()
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
