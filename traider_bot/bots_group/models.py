from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class BotsGroup(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
