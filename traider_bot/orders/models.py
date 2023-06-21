import uuid

from django.db import models


class Order(models.Model):
    CATEGORY_CHOICES = (
        ('linear', 'Linear'),
        # Другие варианты категории ордера
    )

    SIDE_CHOICES = (
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
    )

    ORDER_TYPE_CHOICES = (
        ('Limit', 'Limit'),
        ('Market', 'Market'),
        # Другие варианты типа ордера
    )

    TIME_IN_FORCE_CHOICES = (
        ('GTC', 'Good Till Cancelled'),
        ('IOC', 'Immediate or Cancel'),
        # Другие варианты времени в силе ордера
    )

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='linear')
    symbol = models.CharField(max_length=10)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, default='Buy')
    positionIdx = models.IntegerField(blank=True, null=True)
    orderType = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='Market')
    qty = models.DecimalField(max_digits=10, decimal_places=6)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timeInForce = models.CharField(max_length=3, choices=TIME_IN_FORCE_CHOICES, default='GTC')
    orderLinkId = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.orderLinkId

    def save(self, *args, **kwargs):
        if not self.orderLinkId:
            self.orderLinkId = uuid.uuid4().hex
        super().save(*args, **kwargs)
