from django.db import models
from decimal import Decimal, ROUND_DOWN
from django.core.exceptions import ValidationError
from api_v5 import get_current_price


class Bot(models.Model):
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

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='linear')
    symbol = models.CharField(max_length=100)
    isLeverage = models.IntegerField(default=10)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, default='Buy')
    orderType = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='Limit')
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # triggerDirection = models.IntegerField(null=True)
    # orderFilter = models.CharField(max_length=100, null=True)
    # triggerPrice = models.FloatField(null=True)
    # triggerBy = models.CharField(max_length=10, null=True)
    # orderIv = models.FloatField(null=True)
    # timeInForce = models.CharField(max_length=10, null=True)
    # positionIdx = models.IntegerField(null=True)
    # orderLinkId = models.CharField(max_length=36, null=True)
    # takeProfit = models.FloatField(null=True)
    # stopLoss = models.FloatField(null=True)
    # tpTriggerBy = models.CharField(max_length=10, null=True)
    # slTriggerBy = models.CharField(max_length=10, null=True)
    # reduceOnly = models.BooleanField(default=False)
    # closeOnTrigger = models.BooleanField(default=False)
    # smpType = models.CharField(max_length=10, null=True)
    # mmp = models.BooleanField(default=False)
    # tpslMode = models.CharField(max_length=10, null=True)
    # tpLimitPrice = models.FloatField(null=True)
    # slLimitPrice = models.FloatField(null=True)
    # tpOrderType = models.CharField(max_length=10, null=True)
    # slOrderType = models.CharField(max_length=10, null=True)

    def __str__(self):
        return self.symbol

    # Округляем количество монет вниз чтобы не выйти за предел указанной стоимости
    def get_quantity_from_price(self, qty_USDT):
        current_price = Decimal(get_current_price(self.category, self.symbol))
        return (Decimal(qty_USDT) / current_price).quantize(Decimal('0.001'), rounding=ROUND_DOWN), current_price

    def clean(self):
        if self.orderType == 'Limit' and not self.price:
            raise ValidationError({'price': 'Price is required for Limit order type.'})
