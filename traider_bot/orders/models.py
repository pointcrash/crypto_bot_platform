import math
import uuid

from django.db import models

from api_v5 import *
from bots.models import Bot
from main.models import Log


class Order(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='orders', blank=True, null=True)
    category = models.CharField(default="linear")
    symbol = models.CharField(max_length=10)
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
        print(response)

    def create_teke(self, fraction_length):
        Log.objects.create(content='НЕПОНЯТНО НАХУЯ ВОШЛИ В КРЕАТЕ ТАКЕ')

        symbol_list = get_list(self.bot.account, self.category, self.symbol)
        current_qty = get_qty(symbol_list)
        qty = math.floor((current_qty / 2) * 1000) / 1000
        price = get_position_price(symbol_list)
        side = ("Buy" if get_side(symbol_list) == "Sell" else "Sell")

        if not qty and current_qty:
            take1 = Order.objects.create(
                bot=self.bot,
                category='linear',
                symbol=self.symbol,
                side=side,
                orderType='Limit',
                qty=(qty + 0.001),
                price=round(price * Decimal('1.01'), 2),
                is_take=True,
            )
        elif qty and float(current_qty) % (2 / 10 ** fraction_length) == 0:
            take1 = Order.objects.create(
                bot=self.bot,
                category='linear',
                symbol=self.symbol,
                side=side,
                orderType='Limit',
                qty=qty,
                price=round(price * Decimal('1.01'), 2),
                is_take=True,
            )
            take2 = Order.objects.create(
                bot=self.bot,
                category='linear',
                symbol=self.symbol,
                side=side,
                orderType='Limit',
                qty=qty,
                price=round(price * Decimal('1.02'), 2),
                is_take=True,
            )
        else:
            take1 = Order.objects.create(
                bot=self.bot,
                category='linear',
                symbol=self.symbol,
                side=side,
                orderType='Limit',
                qty=qty,
                price=round(price * Decimal('1.01'), 2),
                is_take=True,
            )
            take2 = Order.objects.create(
                bot=self.bot,
                category='linear',
                symbol=self.symbol,
                side=side,
                orderType='Limit',
                qty=(qty + 0.001),
                price=round(price * Decimal('1.02'), 2),
                is_take=True,
            )

    # def clean(self):
    #     if self.orderType == 'Limit' and not self.price:
    #         raise ValidationError({'price': 'Price is required for Limit order type.'})

    def save(self, *args, **kwargs):

        # Log.objects.create(content='Сохраняем объект ордера')
        if not self.orderLinkId:
            # Log.objects.create(content='Устанавливаем orderLinkId')
            self.orderLinkId = uuid.uuid4().hex
        super().save(*args, **kwargs)
        # Log.objects.create(content='Вызвали метод супер сейв')
        self.realize_order()
        # Log.objects.create(content='отработал релиз ордер')

        # if self.orderType == 'Market':
        #     cancel_all(self.category, self.symbol)
        #     self.create_teke(fraction_length=3)

    def __str__(self):
        return self.orderLinkId
