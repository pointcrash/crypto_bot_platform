import json
import math
import uuid
from decimal import Decimal

from django.db import models

from api_v5 import *
from bots.models import Bot


class Order(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='orders', blank=True, null=True)
    category = models.CharField()
    symbol = models.CharField(max_length=10)
    side = models.CharField()
    positionIdx = models.IntegerField(blank=True, null=True, default=0)
    orderType = models.CharField()
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    timeInForce = models.CharField(default='GTC')
    orderLinkId = models.CharField(max_length=32, unique=True)

    def realize_order(self):
        endpoint = "/v5/order/create"
        method = "POST"

        params = {
            'category': self.category,
            'symbol': self.symbol,
            'side': self.side,
            'positionIdx': self.positionIdx,
            'orderType': self.orderType,
            'qty': str(self.qty),
            'price': str(self.price),
            'timeInForce': self.timeInForce,
            'orderLinkId': self.orderLinkId
        }
        params = json.dumps(params)
        HTTP_Request(endpoint, method, params, "Create")

    def create_teke(self):
        symbol_list = get_list(self.category, self.symbol)
        qty = math.floor((get_qty(symbol_list) / 2) * 1000) / 1000
        price = get_position_price(symbol_list)
        side = ("Buy" if get_positional_side(symbol_list) == "Sell" else "Sell")
        if not qty:
            take1 = Order.objects.create(
                category='linear',
                symbol=self.symbol,
                side=side,
                orderType='Limit',
                qty=(qty+0.001),
                price=round(price * Decimal('1.01'), 2)
            )
        else:
            take1 = Order.objects.create(
                category='linear',
                symbol=self.symbol,
                side=side,
                orderType='Limit',
                qty=qty,
                price=round(price * Decimal('1.01'), 2)
            )
            take2 = Order.objects.create(
                category='linear',
                symbol=self.symbol,
                side=side,
                orderType='Limit',
                qty=(qty+0.001),
                price=round(price * Decimal('1.02'), 2)
            )

    def save(self, *args, **kwargs):

        if not self.orderLinkId:
            self.orderLinkId = uuid.uuid4().hex
        super().save(*args, **kwargs)
        self.realize_order()
###################################################
        cancel_all(self.category, self.symbol)
        self.create_teke()

    def __str__(self):
        return self.orderLinkId
