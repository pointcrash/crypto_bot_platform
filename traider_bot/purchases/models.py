from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

from tariffs.models import Tariff


class ServiceProduct(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    type = models.CharField(max_length=50, default='No type')
    tariff = models.ForeignKey(Tariff, on_delete=models.DO_NOTHING, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.type == 'tariff' and not self.tariff:
            raise ValidationError({'tariff': "Tariff cannot be empty if type is 'tariff'."})

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    product = models.ForeignKey(ServiceProduct, on_delete=models.DO_NOTHING)
    order_id = models.CharField(max_length=32, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    enrolled = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
