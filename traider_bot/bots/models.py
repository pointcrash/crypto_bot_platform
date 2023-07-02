from django.contrib.auth.models import User
from django.db import models
from main.models import Account


class Symbol(models.Model):
    name = models.CharField(max_length=20)
    priceScale = models.CharField(max_length=20, null=True)
    minLeverage = models.CharField(max_length=20, null=True)
    maxLeverage = models.CharField(max_length=20, null=True)
    leverageStep = models.CharField(max_length=20, null=True)
    minPrice = models.CharField(max_length=20, null=True)
    maxPrice = models.CharField(max_length=20, null=True)
    minOrderQty = models.CharField(max_length=20, null=True)

    def __str__(self):
        return self.name


class Bot(models.Model):
    SIDE_CHOICES = (
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
        ('Auto', 'Auto'),
    )

    ORDER_TYPE_CHOICES = (
        ('Limit', 'Limit'),
        ('Market', 'Market'),
        # Другие варианты типа ордера
    )

    MARGIN_TYPE_CHOICES = (
        ('CROSS', 'CROSS'),
        ('ISOLATED', 'ISOLATED'),
        # Другие варианты типа ордера
    )

    KLINE_INTERVAL_CHOICES = (
        ('1', '1'),
        ('3', '3'),
        ('5', '5'),
        ('15', '15'),
        ('30', '30'),
        ('60', '60'),
        ('120', '120'),
        ('240', '240'),
        ('360', '360'),
        ('720', '720'),
        ('D', 'D'),
        ('M', 'M'),
        ('W', 'W'),
    )

    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    account = models.ForeignKey(Account, on_delete=models.DO_NOTHING)
    category = models.CharField(max_length=10, default='linear')
    symbol = models.ForeignKey(Symbol, on_delete=models.DO_NOTHING)
    isLeverage = models.IntegerField(default=10)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, default='Auto')
    orderType = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='Limit')
    qty = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    margin_type = models.CharField(max_length=10, choices=MARGIN_TYPE_CHOICES, default='CROSS')
    qty_kline = models.IntegerField(blank=True, null=True, default=20)
    interval = models.CharField(max_length=3, choices=KLINE_INTERVAL_CHOICES, default='15')
    d = models.IntegerField(blank=True, null=True, default=2)
    process_id = models.CharField(max_length=255, blank=True, null=True, default=None)
    work_model = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.symbol.name
