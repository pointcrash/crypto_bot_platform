from django.db import models


# Create your models here.
class Log(models.Model):
    content = models.CharField()
