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

from bots.models import Symbol
from api_v5 import HTTP_Request, cancel_all, get_qty, get_list, get_side, get_position_price, get_current_price, \
    get_symbol_set
from orders.models import Order


class BollingerBands:
    def __init__(self, account, category: str, symbol_name, symbol_priceScale, interval: int, qty_cline: int, d: int):
        self.account = account
        self.category = category
        self.symbol = symbol_name
        self.priceScale = int(symbol_priceScale)
        self.interval = interval
        self.qty_cline = qty_cline
        self.d = d
        self.kline_list = [[time.time() - 90000]]  # получаем значение времени на 25 часов раньше текущего

    def istime_update_kline(self):
        if datetime.now() - datetime.fromtimestamp(float(self.kline_list[0][0]) / 1000.0) > timedelta(
                minutes=int(self.interval)):
            return True
        return False

    def get_kline(self):
        if not self.istime_update_kline():
            return self.kline_list
        endpoint = "/v5/market/kline"
        method = "GET"
        params = f"category={self.category}&symbol={self.symbol}&interval={self.interval}&limit={self.qty_cline}"
        response = json.loads(HTTP_Request(self.account, endpoint, method, params, "Cline"))
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
        return round(Decimal(sum(self.closePrice_list) / len(self.closePrice_list)), self.priceScale)

    @property
    def std_dev(self):
        return Decimal(statistics.stdev(self.closePrice_list))

    @property
    def tl(self):

        return round(Decimal(self.ml + (self.d * self.std_dev)), self.priceScale)

    @property
    def bl(self):
        return round(Decimal(self.ml - (self.d * self.std_dev)), self.priceScale)


def get_quantity_from_price(qty_USDT, price, minOrderQty):
    return (Decimal(str(qty_USDT)) / price).quantize(Decimal(minOrderQty), rounding=ROUND_DOWN)


def set_entry_point_by_market(bot):
    order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol.name,
        side=bot.side,
        orderType=bot.orderType,
        qty=get_quantity_from_price(bot.qty,
                                    get_current_price(bot.account, bot.category, bot.symbol),
                                    bot.symbol.minOrderQty)
    )


def set_buy_entry_point(bot, bl):
    buy_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol.name,
        side="Buy",
        orderType=bot.orderType,
        qty=get_quantity_from_price(bot.qty, bl - Decimal(bot.symbol.minPrice), bot.symbol.minOrderQty),
        price=bl - Decimal(bot.symbol.minPrice),
    )


def set_sell_entry_point(bot, tl):
    sell_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol.name,
        side="Sell",
        orderType=bot.orderType,
        qty=get_quantity_from_price(bot.qty, tl + Decimal(bot.symbol.minPrice), bot.symbol.minOrderQty),
        price=tl + Decimal(bot.symbol.minPrice),
    )


def set_entry_point(bot, tl, bl):
    if bot.side == "Buy":
        set_buy_entry_point(bot, bl)
    elif bot.side == "Sell":
        set_sell_entry_point(bot, tl)
    elif bot.side == "Auto":
        set_buy_entry_point(bot, bl)
        set_sell_entry_point(bot, tl)


def calculation_entry_point(bot):
    if bot.orderType == "Limit":
        BB_obj = BollingerBands(account=bot.account, category=bot.category, symbol_name=bot.symbol.name,
                                symbol_priceScale=bot.symbol.priceScale, interval=bot.interval,
                                qty_cline=bot.qty_kline, d=bot.d)
    else:
        BB_obj = None
    first_cycle = True

    while True:
        symbol_list = get_list(bot.account, bot.category, bot.symbol)

        if get_qty(symbol_list):
            psn_qty = get_qty(symbol_list)
            psn_side = get_side(symbol_list)
            psn_price = get_position_price(symbol_list)
            print(psn_qty)

            if bot.orderType == "Market" and to_avg_by_market(bot, psn_side, psn_price):
                continue
            print('Дошли до ретурна')
            return psn_qty, psn_side, psn_price, BB_obj, first_cycle

        if bot.orderType == "Market":
            set_entry_point_by_market(bot)
            first_cycle = False
            continue

        tl = BB_obj.tl
        bl = BB_obj.bl

        if not first_cycle:
            time.sleep(10)

        if first_cycle or tl != BB_obj.tl or bl != BB_obj.bl:
            cancel_all(bot.account, bot.category, bot.symbol)
            set_entry_point(bot, tl, bl)

        first_cycle = False


def set_takes(bot):
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)
    current_price = get_current_price(bot.account, bot.category, bot.symbol)
    set_takes_qty = 0
    while True:
        psn_qty, psn_side, psn_price, BB_obj, first_cycle = calculation_entry_point(bot)

        tl = BB_obj.tl
        bl = BB_obj.bl

        if first_cycle:  # Not first cycle (-_-)
            time.sleep(10)

        if not first_cycle or set_takes_qty != psn_qty or tl != BB_obj.tl or bl != BB_obj.bl:
            cancel_all(bot.account, bot.category, bot.symbol)

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
                    category=bot.category,
                    symbol=bot.symbol.name,
                    side=side,
                    orderType='Limit',
                    qty=(qty + (1 / 10 ** fraction_length)),
                    price=round(exit_line, round_number),
                    is_take=True,
                )
            elif qty and (psn_qty * (10 ** fraction_length)) % 2 == 0:
                if current_price < ml:
                    take1 = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType='Limit',
                        qty=qty,
                        price=round(ml, round_number),
                        is_take=True,
                    )
                    take2 = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType='Limit',
                        qty=qty,
                        price=round(exit_line, round_number),
                        is_take=True,
                    )
                else:
                    take2 = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType='Limit',
                        qty=psn_qty,
                        price=round(exit_line, round_number),
                        is_take=True,
                    )
            else:
                if current_price < ml:
                    take1 = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType='Limit',
                        qty=qty,
                        price=round(ml, round_number),
                        is_take=True,
                    )
                    take2 = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType='Limit',
                        qty=(qty + (1 / 10 ** fraction_length)),
                        price=round(exit_line, round_number),
                        is_take=True,
                    )
                else:
                    take2 = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType='Limit',
                        qty=psn_qty,
                        price=round(exit_line, round_number),
                        is_take=True,
                    )
        set_takes_qty = psn_qty


def to_avg_by_market(bot, side, psn_price):
    current_price = get_current_price(bot.account, bot.category, bot.symbol)
    if side == "Buy":
        if psn_price - current_price > psn_price * Decimal('0.01'):
            print('avg')
            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol.name,
                side=side,
                orderType="Market",
                qty=get_quantity_from_price(bot.qty, current_price, bot.symbol.minOrderQty),
            )
            return True
        else:
            return False

    if side == "Sell":
        if current_price - psn_price > psn_price * Decimal('0.01'):
            print('avg')

            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol.name,
                side=side,
                orderType="Market",
                qty=get_quantity_from_price(bot.qty, current_price, bot.symbol.minOrderQty),
            )
            return True
        else:
            return False


def get_update_symbols():
    symbol_set = get_symbol_set()
    Symbol.objects.all().delete()
    for symbol in symbol_set:
        Symbol.objects.create(
            name=symbol[0],
            priceScale=symbol[1],
            minLeverage=symbol[2],
            maxLeverage=symbol[3],
            leverageStep=symbol[4],
            minPrice=symbol[5],
            maxPrice=symbol[6],
            minOrderQty=symbol[7],
        )


def count_decimal_places(number):
    decimal_tuple = number.as_tuple()
    decimal_places = -decimal_tuple.exponent
    return decimal_places
