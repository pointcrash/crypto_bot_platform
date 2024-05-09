from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

from main.models import Account, ExchangeService


class Symbol(models.Model):
    name = models.CharField(max_length=20)
    service = models.ForeignKey(ExchangeService, on_delete=models.SET_NULL, null=True)
    priceScale = models.CharField(max_length=20, null=True)
    minLeverage = models.CharField(max_length=20, null=True)
    maxLeverage = models.CharField(max_length=20, null=True)
    leverageStep = models.CharField(max_length=20, null=True)
    minPrice = models.CharField(max_length=20, null=True)
    maxPrice = models.CharField(max_length=20, null=True)
    tickSize = models.CharField(max_length=20, null=True)
    minOrderQty = models.CharField(max_length=20, null=True)
    maxOrderQty = models.CharField(max_length=20, null=True)
    qtyStep = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name


class BotModel(models.Model):
    MARGIN_TYPE_CHOICES = (
        ('CROSS', 'CROSS'),
        ('ISOLATED', 'ISOLATED'),
    )

    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    account = models.ForeignKey(Account, on_delete=models.DO_NOTHING)
    category = models.CharField(max_length=10, default='linear', blank=True)
    symbol = models.ForeignKey(Symbol, on_delete=models.DO_NOTHING)
    leverage = models.IntegerField(default=10)
    amount_long = models.IntegerField(validators=[MinValueValidator(0)])
    amount_short = models.IntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    margin_type = models.CharField(max_length=10, choices=MARGIN_TYPE_CHOICES, default='CROSS', blank=True)
    work_model = models.CharField(max_length=10)
    pnl = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True, default=0)

    is_active = models.BooleanField(default=False)
    time_create = models.DateTimeField(auto_now_add=True, null=True)
    time_update = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = ['account', 'symbol']

    def __str__(self):
        return self.symbol.name


class SoftDeletedModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Log(models.Model):
    objects = SoftDeletedModelManager()
    soft_deleted_objects = models.Manager()

    bot = models.ForeignKey(BotModel, on_delete=models.SET_NULL, blank=True, null=True)
    content = models.CharField(blank=True, null=True)
    time = models.CharField(blank=True, null=True)
    time_create = models.DateTimeField(auto_now_add=True, null=True)
    is_deleted = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


class BBBotModel(models.Model):
    SIDE_CHOICES = (
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
        ('FB', 'First Band'),
    )

    ORDER_TYPE_CHOICES = (
        ('Limit', 'Limit'),
        ('Market', 'Market'),
        # Другие варианты типа ордера
    )

    HARD_AVG_TYPE_CHOICES = (
        ('pnl', 'Убытки (PnL)'),
        ('percent', 'Изменение цены'),
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
        ('W', 'W'),
        ('M', 'M'),
    )
    bot = models.OneToOneField(BotModel, on_delete=models.CASCADE, related_name='bb', blank=True, null=True)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, default='FB')
    orderType = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='Limit', blank=True)
    qty_kline = models.IntegerField(default=20)
    interval = models.CharField(max_length=3, choices=KLINE_INTERVAL_CHOICES, default='15')
    d = models.IntegerField(default=2)
    take_on_ml = models.BooleanField(default=True)
    take_on_ml_percent = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    take_on_ml_status = models.BooleanField(default=False, blank=True, null=True)
    take_on_ml_qty = models.DecimalField(max_digits=10, decimal_places=5, default=0, blank=True, null=True)
    auto_avg = models.BooleanField(default=False)
    avg_percent = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    is_deviation_from_lines = models.BooleanField(default=False, blank=True)
    percent_deviation_from_lines = models.DecimalField(max_digits=10, decimal_places=5, default=0, blank=True)
    dfm = models.DecimalField(max_digits=5, decimal_places=3, default=70)
    chw = models.DecimalField(max_digits=5, decimal_places=3, default=2)
    dfep = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    max_margin = models.IntegerField(null=True, blank=True)

    hard_avg = models.BooleanField(default=False)
    hard_avg_type = models.CharField(choices=HARD_AVG_TYPE_CHOICES, null=True, blank=True)
    hard_avg_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    time_create = models.DateTimeField(auto_now_add=True, null=True)
    time_update = models.DateTimeField(auto_now=True, null=True)


class Set0Psn(models.Model):
    bot = models.OneToOneField(BotModel, on_delete=models.CASCADE, blank=True, null=True)
    set0psn = models.BooleanField(default=False)
    trend = models.IntegerField(blank=True, null=True)
    limit_pnl_loss_s0n = models.CharField(blank=True, null=True)
    max_margin_s0p = models.CharField(blank=True, null=True)


class SimpleHedge(models.Model):
    bot = models.OneToOneField(BotModel, on_delete=models.CASCADE, blank=True, null=True)
    tppp = models.CharField(blank=True, null=True)
    tpap = models.CharField(blank=True, null=True)
    tp_count = models.IntegerField(blank=True, null=True, default=1)


class StepHedge(models.Model):
    TP_TRAILING_PERCENT_CHOICES = (
        ('0.1', '0.1'),
        ('0.2', '0.2'),
        ('0.3', '0.3'),
        ('0.5', '0.5'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('5', '5'),
        ('10', '10'),
    )

    bot = models.OneToOneField(BotModel, on_delete=models.CASCADE, blank=True, null=True, related_name='zinger')
    short1invest = models.IntegerField(blank=True, null=True)
    long1invest = models.IntegerField(blank=True, null=True)
    income_percent = models.DecimalField(max_digits=4, decimal_places=1, default=6)
    tp_pnl_percent_short = models.DecimalField(max_digits=4, decimal_places=1)
    tp_pnl_percent_long = models.DecimalField(max_digits=4, decimal_places=1)
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=10, default=0)
    pnl_short_avg = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    pnl_long_avg = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    margin_short_avg = models.IntegerField(blank=True, null=True)
    margin_long_avg = models.IntegerField(blank=True, null=True)
    qty_steps = models.IntegerField(default=30, blank=True)
    qty_steps_diff = models.IntegerField(default=10, blank=True)
    add_tp = models.BooleanField(default=False, blank=True)
    is_nipple_active = models.BooleanField(default=False, blank=True, null=True)
    tp_trailing = models.BooleanField(default=False, blank=True, null=True)
    tp_trailing_percent = models.CharField(max_length=5, choices=TP_TRAILING_PERCENT_CHOICES, default='1')
    move_nipple = models.BooleanField(blank=True, null=True)

    def set_move_nipple_value(self):
        if self.move_nipple is None:
            self.move_nipple = True if self.is_nipple_active is True else False

    def save(self, *args, **kwargs):
        self.set_move_nipple_value()
        super().save(*args, **kwargs)


class OppositePosition(models.Model):
    bot = models.OneToOneField(BotModel, on_delete=models.CASCADE, blank=True, null=True)
    activate_opp = models.BooleanField(default=False)
    limit_pnl_loss_opp = models.CharField(blank=True, null=True)
    psn_qty_percent_opp = models.CharField(blank=True, null=True)
    max_margin_opp = models.CharField(blank=True, null=True)


class JsonObjectClass(models.Model):
    bot = models.OneToOneField(BotModel, on_delete=models.CASCADE, blank=True, null=True)
    bot_mode = models.CharField(blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
