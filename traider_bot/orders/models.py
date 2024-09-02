from decimal import Decimal

from django.db import models

from bots.models import BotModel, Symbol
from main.models import Account


class Order(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    bot = models.ForeignKey(BotModel, on_delete=models.DO_NOTHING, null=True)
    symbol = models.ForeignKey(Symbol, on_delete=models.DO_NOTHING, null=True)
    symbol_name = models.CharField()
    order_id = models.CharField()
    client_order_id = models.CharField(null=True)
    side = models.CharField(null=True)
    qty = models.CharField(null=True)
    price = models.CharField(null=True)
    avg_price = models.CharField(null=True)
    trigger_price = models.CharField(null=True)
    trigger_direction = models.CharField(null=True)
    status = models.CharField(null=True)
    psn_side = models.CharField(null=True)
    reduce_only = models.BooleanField(null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.symbol_name


class Position(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    bot = models.ForeignKey(BotModel, on_delete=models.DO_NOTHING, null=True)
    symbol = models.ForeignKey(Symbol, on_delete=models.DO_NOTHING, null=True)
    symbol_name = models.CharField()
    side = models.CharField(null=True)
    qty = models.CharField(null=True)
    cost = models.CharField(null=True)
    entry_price = models.CharField(null=True)
    unrealised_pnl = models.CharField(null=True)
    realised_pnl = models.CharField(null=True)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.cost = str(Decimal(self.qty) * Decimal(self.entry_price))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.symbol_name
