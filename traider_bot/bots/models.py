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
    maxOrderQty = models.CharField(max_length=20, null=True)

    def __str__(self):
        return self.name


class Bot(models.Model):
    SIDE_CHOICES = (
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
        ('FB', 'First Band'),
        ('TS', 'Two-Sided'),
    )

    CATEGORY_CHOICES = (
        ('linear', 'linear'),
        ('inverse', 'inverse'),
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
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='linear')
    symbol = models.ForeignKey(Symbol, on_delete=models.DO_NOTHING)
    isLeverage = models.IntegerField(default=10)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, default='Auto')
    orderType = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='Limit')
    qty = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    margin_type = models.CharField(max_length=10, choices=MARGIN_TYPE_CHOICES, default='CROSS')
    qty_kline = models.IntegerField(blank=True, null=True, default=20)
    interval = models.CharField(max_length=3, choices=KLINE_INTERVAL_CHOICES, default='15')
    d = models.IntegerField(blank=True, null=True, default=2)
    process_id = models.CharField(max_length=255, blank=True, null=True, default=None)
    work_model = models.CharField(max_length=10, null=True, blank=True)
    take_on_ml = models.BooleanField(default=True)
    take_on_ml_percent = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    auto_avg = models.BooleanField(default=True)
    bb_avg_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    grid_avg_value = models.DecimalField(max_digits=5, decimal_places=3, default=1)
    grid_profit_value = models.DecimalField(max_digits=5, decimal_places=3, default=1)
    grid_take_count = models.IntegerField(default=2)
    is_percent_deviation_from_lines = models.BooleanField(default=False)
    deviation_from_lines = models.DecimalField(max_digits=10, decimal_places=5, default=0)
    dfm = models.DecimalField(max_digits=5, decimal_places=3, default=30)
    chw = models.DecimalField(max_digits=5, decimal_places=3, default=2)
    max_margin = models.IntegerField(null=True, blank=True)
    time_sleep = models.IntegerField(default=5, null=True, blank=True)
    firs_take_is_done = models.BooleanField(default=False)

    entry_order_sell = models.CharField(blank=True, null=True)
    entry_order_sell_amount = models.DecimalField(max_digits=10, decimal_places=10, blank=True, null=True)
    entry_order_by = models.CharField(blank=True, null=True)
    entry_order_by_amount = models.DecimalField(max_digits=10, decimal_places=10, blank=True, null=True)
    take1 = models.CharField(blank=True, null=True)
    take2 = models.CharField(blank=True, null=True)
    take2_amount = models.DecimalField(max_digits=10, decimal_places=10, blank=True, null=True)
    pnl = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True, default=0)

    repeat = models.BooleanField(default=False)

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    class Meta:
        unique_together = ['account', 'symbol']

    def __str__(self):
        return self.symbol.name


class Take(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, blank=True, null=True)
    take_number = models.SmallIntegerField(blank=True, null=True)
    order_link_id = models.CharField(default='', blank=True, null=True)
    is_filled = models.BooleanField(default=False, blank=True, null=True)


class Log(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, blank=True, null=True)
    content = models.CharField(blank=True, null=True)


class Process(models.Model):
    pid = models.CharField(blank=True, null=True, default=None)
    bot = models.OneToOneField(Bot, on_delete=models.CASCADE)


class AvgOrder(models.Model):
    bot = models.OneToOneField(Bot, on_delete=models.CASCADE, blank=True, null=True)
    order_link_id = models.CharField(default='', blank=True, null=True)
    is_filled = models.BooleanField(default=False, blank=True, null=True)


class SingleBot(models.Model):
    bot = models.OneToOneField(Bot, on_delete=models.CASCADE, blank=True, null=True)
    single = models.BooleanField(default=False)


class IsTSStart(models.Model):
    bot = models.OneToOneField(Bot, on_delete=models.CASCADE, blank=True, null=True)
    TS = models.BooleanField(default=False)

