from django.core.exceptions import ValidationError
from django.db import models

from api_v5 import *
from bots.models import Bot


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

    def create_teke(self, fraction_length):
        symbol_list = get_list(self.category, self.symbol)
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
                qty=(qty+0.001),
                price=round(price * Decimal('1.01'), 2),
                is_take=True,
            )
        elif qty and float(current_qty) % (2 / 10**fraction_length) == 0:
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
                qty=(qty+0.001),
                price=round(price * Decimal('1.02'), 2),
                is_take=True,
            )

    # def clean(self):
    #     if self.orderType == 'Limit' and not self.price:
    #         raise ValidationError({'price': 'Price is required for Limit order type.'})

    def save(self, *args, **kwargs):

        if not self.orderLinkId:
            self.orderLinkId = uuid.uuid4().hex
        super().save(*args, **kwargs)
        self.realize_order()

        # if self.orderType == 'Market':
        #     cancel_all(self.category, self.symbol)
        #     self.create_teke(fraction_length=3)

    def __str__(self):
        return self.orderLinkId
