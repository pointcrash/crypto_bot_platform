import uuid
from datetime import datetime, timedelta

import pytz
from django.db import models

from api.api_v5_bybit import *
from bots.models import Bot, Log
from timezone.models import TimeZone


class Order(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='orders', blank=True, null=True)
    category = models.CharField(default="linear")
    symbol = models.CharField()
    isLeverage = models.IntegerField(default=10)
    side = models.CharField()
    positionIdx = models.IntegerField(blank=True, null=True, default=0)
    orderType = models.CharField()
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    char_price = models.CharField(blank=True, null=True)
    timeInForce = models.CharField(default='GTC')
    orderLinkId = models.CharField(max_length=32, unique=True)
    is_take = models.BooleanField(default=False)
    takeProfit = models.CharField(max_length=32, blank=True, null=True, default='')
    stopLoss = models.CharField(max_length=32, blank=True, null=True, default='')
    triggerPrice = models.CharField(max_length=32, blank=True, null=True, default='')
    triggerDirection = models.CharField(max_length=32, blank=True, null=True, default='')

    def realize_order(self):
        price = self.price if self.price else self.char_price

        endpoint = "/v5/order/create"
        method = "POST"
        params = {
            'category': 'linear',
            'symbol': self.symbol,
            'side': self.side,
            'positionIdx': self.positionIdx,
            'orderType': self.orderType,
            'qty': str(self.qty),
            'price': str(price),
            'orderLinkId': self.orderLinkId,
        }

        if self.takeProfit:
            params['takeProfit'] = self.takeProfit
        if self.stopLoss:
            params['stopLoss'] = self.stopLoss
        if self.triggerPrice and self.triggerDirection:
            params['triggerDirection'] = self.triggerDirection
            params['triggerPrice'] = self.triggerPrice

        params = json.dumps(params)
        response = HTTP_Request(self.bot.account, endpoint, method, params, bot=self.bot)
        bot = Bot.objects.get(pk=self.bot.pk)
        logging(bot, f'{params}')
        logging(bot, f'{response}')
        # print('Order ----')
        # print(response)
        # print(params)
        # print('Order ----')
        # print('')

    def save(self, *args, **kwargs):
        if not self.positionIdx:
            if self.is_take:
                self.positionIdx = 2 if self.side == 'Buy' else 1
            else:
                self.positionIdx = 1 if self.side == 'Buy' else 2
        if not self.orderLinkId:
            self.orderLinkId = uuid.uuid4().hex
        super().save(*args, **kwargs)
        self.realize_order()

    def __str__(self):
        return self.orderLinkId


def logging(bot, text):
    user = bot.owner
    timezone = TimeZone.objects.filter(users=user).first()
    gmt0 = pytz.timezone('GMT')
    date = datetime.now(gmt0).replace(microsecond=0)
    bot_info = f'Bot {bot.pk} {bot.symbol.name} {bot.side} {bot.interval}'
    gmt = 0

    if timezone:
        gmt = int(timezone.gmtOffset)
        if gmt > 0:
            date = date + timedelta(seconds=gmt)
        else:
            date = date - timedelta(seconds=gmt)

    if gmt > 0:
        str_gmt = '+' + str(gmt / 3600)
    elif gmt < 0:
        str_gmt = str(gmt / 3600)
    else:
        str_gmt = str(gmt)

    in_time = f'{date.time()} | {date.date()}'
    Log.objects.create(bot=bot, content=f'{bot_info} {text}', time=f'{in_time} (GMT {str_gmt})')
