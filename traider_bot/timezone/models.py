from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class TimeZone(models.Model):
    users = models.ManyToManyField(User)
    countryCode = models.CharField()
    countryName = models.CharField()
    zoneName = models.CharField()
    gmtOffset = models.CharField()

    def __str__(self):
        gmt = int(int(self.gmtOffset) / 3600)
        if gmt > 0:
            gmt = '+' + str(gmt)

        return f"{self.zoneName} (GMT {gmt})"
