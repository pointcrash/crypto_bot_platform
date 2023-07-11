import math
import uuid

from django.db import models

from api_v5 import *
from bots.models import Bot


class Order(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='orders', blank=True, null=True)
    category = models.CharField(default="linear")
    symbol = models.CharField(max_length=10)
    isLeverage = models.IntegerField(default=10)
    side = models.CharField()
    positionIdx = models.IntegerField(blank=True, null=True, default=0)
    orderType = models.CharField()
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    timeInForce = models.CharField(default='GTC')
    orderLinkId = models.CharField(max_length=32, unique=True)
    is_take = models.BooleanField(default=False)

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
            # 'timeInForce': self.timeInForce,
            'orderLinkId': self.orderLinkId
        }
        params = json.dumps(params)
        response = HTTP_Request(self.bot.account, endpoint, method, params, "Create")
        print(response)
        print(params)

    def save(self, *args, **kwargs):
        if self.category == 'inverse':
            if self.side == 'Buy':
                self.positionIdx = 1
            else:
                self.positionIdx = 2
        if not self.orderLinkId:
            self.orderLinkId = uuid.uuid4().hex
        super().save(*args, **kwargs)
        self.realize_order()

    def __str__(self):
        return self.orderLinkId
