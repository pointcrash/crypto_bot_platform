from django.db import models


# Create your models here.
class Log(models.Model):
    content = models.CharField()


class Account(models.Model):
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

