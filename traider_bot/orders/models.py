import json
import uuid
from decimal import Decimal

from django.db import models

from api_v5 import HTTP_Request, get_price_BTC, get_qty_BTC, get_position_price_BTC, cancel_all, get_BTC_list


class Order(models.Model):
    CATEGORY_CHOICES = (
        ('linear', 'Linear'),
        # Другие варианты категории ордера
    )

    SIDE_CHOICES = (
        ('Buy', 'Buy'),
        ('Sell', 'Sell'),
    )

    ORDER_TYPE_CHOICES = (
        ('Limit', 'Limit'),
        ('Market', 'Market'),
        # Другие варианты типа ордера
    )

    TIME_IN_FORCE_CHOICES = (
        ('GTC', 'Good Till Cancelled'),
        ('IOC', 'Immediate or Cancel'),
        # Другие варианты времени в силе ордера
    )

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='linear')
    symbol = models.CharField(max_length=10)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, default='Buy')
    positionIdx = models.IntegerField(blank=True, null=True, default=0)
    orderType = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES, default='Market')
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    timeInForce = models.CharField(max_length=3, choices=TIME_IN_FORCE_CHOICES, default='GTC')
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

    def create_teke_on_sell(self):
        qty = round(get_qty_BTC(get_BTC_list()) / 2, 3)
        price = get_position_price_BTC(get_BTC_list())
        take1 = Order.objects.create(
            category='linear',
            symbol=self.symbol,
            side='Sell',
            orderType='Limit',
            qty=qty,
            price=round(price * Decimal('1.01'), 2)
        )
        take2 = Order.objects.create(
            category='linear',
            symbol=self.symbol,
            side='Sell',
            orderType='Limit',
            qty=qty,
            price=round(price * Decimal('1.02'), 2)
        )

    def save(self, *args, **kwargs):

        if not self.orderLinkId:
            self.orderLinkId = uuid.uuid4().hex
        super().save(*args, **kwargs)
        self.realize_order()

        if self.price is None and self.orderType == 'Market':
            self.price = get_price_BTC()
            super().save(*args, **kwargs)

        if self.orderType == 'Market' and self.side == 'Buy':
            cancel_all()
            self.create_teke_on_sell()

    def __str__(self):
        return self.orderLinkId
