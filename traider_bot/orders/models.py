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
        # Log.objects.create(content='Зашли в релиз ордер')

        endpoint = "/v5/order/create"
        method = "POST"
        params = {
            'category': self.category,
            'symbol': self.symbol,
            'isLeverage': self.isLeverage,
            'side': self.side,
            'positionIdx': self.positionIdx,
            'orderType': self.orderType,
            'qty': str(self.qty),
            'price': str(self.price),
            'timeInForce': self.timeInForce,
            'orderLinkId': self.orderLinkId
        }
        # Log.objects.create(content='сформировали параметры')
        params = json.dumps(params)
        # Log.objects.create(content='дамп параметров в строку')
        response = HTTP_Request(self.bot.account, endpoint, method, params, "Create")
        # Log.objects.create(content='отправили запрос на создание ордера, все ОК')
        # print(params)
        print(response)

    def save(self, *args, **kwargs):
        # Log.objects.create(content='Сохраняем объект ордера')
        if not self.orderLinkId:
            # Log.objects.create(content='Устанавливаем orderLinkId')
            self.orderLinkId = uuid.uuid4().hex
        super().save(*args, **kwargs)
        # Log.objects.create(content='Вызвали метод супер сейв')
        self.realize_order()
        # Log.objects.create(content='отработал релиз ордер')

    def __str__(self):
        return self.orderLinkId
