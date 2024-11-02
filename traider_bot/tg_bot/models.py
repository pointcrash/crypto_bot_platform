from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class TelegramAccount(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    chat_id = models.CharField(null=True, blank=True)
    telegram_username = models.CharField()

