from django.db import models


# Create your models here.
class Log(models.Model):
    content = models.CharField()


class Account(models.Model):
    name = models.CharField()
    API_TOKEN = models.CharField()
    SECRET_KEY = models.CharField()
    is_mainnet = models.BooleanField()
