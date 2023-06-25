import json
import math
import statistics
import time
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from api_v5 import HTTP_Request, cancel_all, get_qty, get_list, get_side, get_position_price, get_current_price
from orders.models import Order


class BollingerBands:
    def __init__(self, category: str, symbol: str, interval: int, qty_cline: int, d: int):
        self.category = category
        self.symbol = symbol
        self.interval = interval
        self.qty_cline = qty_cline
        self.d = d
        self.kline_list = [[time.time() - 90000]]  # получаем значение времени на 25 часов раньше текущего

    def istime_update_kline(self):
        if datetime.now() - datetime.fromtimestamp(float(self.kline_list[0][0]) / 1000.0) > timedelta(
                minutes=self.interval):
            return True
        return False

    def get_kline(self):
        if not self.istime_update_kline():
            return self.kline_list
        endpoint = "/v5/market/kline"
        method = "GET"
        params = f"category={self.category}&symbol={self.symbol}&interval={self.interval}&limit={self.qty_cline}"
        response = json.loads(HTTP_Request(endpoint, method, params, "Cline"))
        self.kline_list = response["result"]["list"]
        return response["result"]["list"]

    @property
    def closePrice_list(self):
        closePrice_list = []
        for i in self.get_kline():
            closePrice_list.append(Decimal(i[4]))
        return closePrice_list

    @property
    def ml(self):
        return Decimal(sum(self.closePrice_list) / len(self.closePrice_list))

    @property
    def std_dev(self):
        return Decimal(statistics.stdev(self.closePrice_list))

    @property
    def tl(self):
        return Decimal(self.ml + (self.d * self.std_dev))

    @property
    def bl(self):
        return Decimal(self.ml - (self.d * self.std_dev))


a = BollingerBands("linear", "BTCUSDT", 15, 20, 2)


def get_quantity_from_price(qty_USDT, price):
    return (Decimal(str(qty_USDT)) / price).quantize(Decimal('0.001'), rounding=ROUND_DOWN)


def set_entry_point(bot, tl, bl):
    sell_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol,
        side="Sell",
        orderType="Limit",
        qty=get_quantity_from_price(bot.qty, tl+1),
        price=tl + 1,
    )

    buy_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol,
        side="Buy",
        orderType="Limit",
        qty=get_quantity_from_price(bot.qty, bl-1),
        price=bl - 1,
    )


def calculation_entry_point(bot):
    BB_obj = BollingerBands(bot.category, bot.symbol, bot.interval, bot.qty_kline, bot.d)
    first_cycle = True

    while True:
        symbol_list = get_list(bot.category, bot.symbol)
        if get_qty(symbol_list):
            cancel_all(bot.category, bot.symbol)
            return get_qty(symbol_list), get_side(symbol_list), get_position_price(symbol_list), BB_obj, first_cycle

        tl = BB_obj.tl
        bl = BB_obj.bl

        if not first_cycle:
            time.sleep(30)

        if first_cycle or tl != BB_obj.tl or bl != BB_obj.bl:
            cancel_all(bot.category, bot.symbol)
            set_entry_point(bot, tl, bl)

        first_cycle = False


def set_takes(bot, fraction_length=3):
    while True:
        psn_qty, psn_side, psn_price, BB_obj, first_cycle = calculation_entry_point(bot)

        tl = BB_obj.tl
        bl = BB_obj.bl

        if first_cycle:
            time.sleep(30)

        if not first_cycle or tl != BB_obj.tl or bl != BB_obj.bl:
            cancel_all(bot.category, bot.symbol)

            side = "Buy" if psn_side == "Sell" else "Sell"
            qty = math.floor((psn_qty / 2) * 10 ** fraction_length) / 10 ** fraction_length

            if side == "Buy":
                ml = BB_obj.ml
                exit_line = BB_obj.bl
            else:
                ml = BB_obj.ml
                exit_line = BB_obj.tl

            if not qty and psn_qty:
                take1 = Order.objects.create(
                    bot=bot,
                    category='linear',
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=(qty + (1 / 10 ** fraction_length)),
                    price=round(exit_line, 2),
                    is_take=True,
                )
            elif qty and float(psn_qty) % (2 / 10 ** fraction_length) == 0:
                take1 = Order.objects.create(
                    bot=bot,
                    category='linear',
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=round(ml, 2),
                    is_take=True,
                )
                take2 = Order.objects.create(
                    bot=bot,
                    category='linear',
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=round(exit_line, 2),
                    is_take=True,
                )
            else:
                take1 = Order.objects.create(
                    bot=bot,
                    category='linear',
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=round(ml, 2),
                    is_take=True,
                )
                take2 = Order.objects.create(
                    bot=bot,
                    category='linear',
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=(qty + (1 / 10 ** fraction_length)),
                    price=round(exit_line, 2),
                    is_take=True,
                )
