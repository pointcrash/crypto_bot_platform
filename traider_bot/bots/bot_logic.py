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

from main.models import Log
from api_v5 import HTTP_Request, cancel_all, get_qty, get_list, get_side, get_position_price, get_current_price
from orders.models import Order


class BollingerBands:
    def __init__(self, account, category: str, symbol: str, interval: int, qty_cline: int, d: int):
        self.account = account
        self.category = category
        self.symbol = symbol
        self.interval = interval
        self.qty_cline = qty_cline
        self.d = d
        self.kline_list = [[time.time() - 90000]]  # получаем значение времени на 25 часов раньше текущего

    def istime_update_kline(self):
        # Log.objects.create(content='Проверяем не время ли обновить данные по ВВ')
        if datetime.now() - datetime.fromtimestamp(float(self.kline_list[0][0]) / 1000.0) > timedelta(minutes=int(self.interval)):
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
        # Log.objects.create(content='Получили пакет свечей')
        return response["result"]["list"]

    @property
    def closePrice_list(self):
        closePrice_list = []
        for i in self.get_kline():
            closePrice_list.append(Decimal(i[4]))
        # Log.objects.create(content='Сформирован список закрывающих цен')
        return closePrice_list

    @property
    def ml(self):
        # Log.objects.create(content='получение МЛ')
        return round(Decimal(sum(self.closePrice_list) / len(self.closePrice_list)), 2)

    @property
    def std_dev(self):
        # Log.objects.create(content='получение стд_дев')
        return Decimal(statistics.stdev(self.closePrice_list))

    @property
    def tl(self):

        # Log.objects.create(content='получение ТЛ')

        return round(Decimal(self.ml + (self.d * self.std_dev)), 2)

    @property
    def bl(self):
        # Log.objects.create(content='Получение БЛ')
        return round(Decimal(self.ml - (self.d * self.std_dev)), 2)


# a = BollingerBands("linear", "BTCUSDT", 15, 20, 2)


def get_quantity_from_price(qty_USDT, price):
    # Log.objects.create(content='Расчитываем количество монет которое можно купить')
    return (Decimal(str(qty_USDT)) / price).quantize(Decimal('0.001'), rounding=ROUND_DOWN)


def set_buy_entry_point(bot, bl):
    buy_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol,
        side="Buy",
        orderType="Limit",
        qty=get_quantity_from_price(bot.qty, bl - 1),
        price=bl - 1,
    )
    # Log.objects.create(content='Создали ордер на лонг')


def set_sell_entry_point(bot, tl):
    sell_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol,
        side="Sell",
        orderType="Limit",
        qty=get_quantity_from_price(bot.qty, tl + 1),
        price=tl + 1,
    )
    # Log.objects.create(content='Создали ордер на шорт')


def set_entry_point(bot, tl, bl):
    if bot.side == "Buy":
        set_buy_entry_point(bot, bl)
    elif bot.side == "Sell":
        set_sell_entry_point(bot, tl)
    elif bot.side == "Auto":
        set_buy_entry_point(bot, bl)
        set_sell_entry_point(bot, tl)


def calculation_entry_point(bot):
    # Log.objects.create(content='Функция calculation_entry_point - вход')

    BB_obj = BollingerBands(bot.account, bot.category, bot.symbol, bot.interval, bot.qty_kline, bot.d)
    first_cycle = True
    # Log.objects.create(content='Создан объект ВВ')

    while True:
        symbol_list = get_list(bot.account, bot.category, bot.symbol)
        # Log.objects.create(content='Получение данных по позиции')

        if get_qty(symbol_list):
            psn_qty = get_qty(symbol_list)
            psn_side = get_side(symbol_list)
            psn_price = get_position_price(symbol_list)
            # Log.objects.create(content='Сработал ордер на вход, позиция открыта')

            if to_avg(bot, psn_side, psn_price):
                continue

            return psn_qty, psn_side, psn_price, BB_obj, first_cycle

        tl = BB_obj.tl
        bl = BB_obj.bl

        if not first_cycle:
            # Log.objects.create(content='Смотрим за ценами на вход, ждем 30 сек')
            time.sleep(30)

        if first_cycle or tl != BB_obj.tl or bl != BB_obj.bl:
            # Log.objects.create(content='Первый цикл входа или тл бл изменилось')
            cancel_all(bot.account, bot.category, bot.symbol)
            set_entry_point(bot, tl, bl)

        first_cycle = False


def set_takes(bot, fraction_length=3):
    # Log.objects.create(content='Функция set_takes - вход')
    set_takes_qty = 0
    while True:
        psn_qty, psn_side, psn_price, BB_obj, first_cycle = calculation_entry_point(bot)
        # Log.objects.create(content='Цикл calculation_entry_point отработал, выставляем тейки')

        tl = BB_obj.tl
        bl = BB_obj.bl

        if first_cycle:  # Not first cycle (-_-)
            # Log.objects.create(content='Проверка на первый цикл не прошла, ждем 30 сек')
            time.sleep(30)

        if not first_cycle or set_takes_qty != psn_qty or tl != BB_obj.tl or bl != BB_obj.bl:
            # Log.objects.create(content='Перый цикл тейков или тл бл изменились')
            cancel_all(bot.account, bot.category, bot.symbol)

            side = "Buy" if psn_side == "Sell" else "Sell"
            qty = math.floor((psn_qty / 2) * 10 ** fraction_length) / 10 ** fraction_length

            if side == "Buy":
                ml = BB_obj.ml
                exit_line = BB_obj.bl
                # Log.objects.create(content='Вошли на лонг значит exit_line = бл')
            else:
                ml = BB_obj.ml
                exit_line = BB_obj.tl
                # Log.objects.create(content='Вошли на шорт значит exit_line = тл')

            if not qty and psn_qty:
                take1 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=(qty + (1 / 10 ** fraction_length)),
                    price=round(exit_line, 2),
                    is_take=True,
                )
                # Log.objects.create(content='Создан один тейк not qty and psn_qty')
            elif qty and float(psn_qty) % (2 / 10 ** fraction_length) == 0:
                take1 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=round(ml, 2),
                    is_take=True,
                )
                take2 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=round(exit_line, 2),
                    is_take=True,
                )
                # Log.objects.create(content='qty and float(psn_qty) % (2 / 10 ** fraction_length) == 0')
            else:
                take1 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=qty,
                    price=round(ml, 2),
                    is_take=True,
                )
                take2 = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol,
                    side=side,
                    orderType='Limit',
                    qty=(qty + (1 / 10 ** fraction_length)),
                    price=round(exit_line, 2),
                    is_take=True,
                )
                # Log.objects.create(content='созданы тейки по нечетной позиции')
        set_takes_qty = psn_qty


def to_avg(bot, side, psn_price):
    current_price = get_current_price(bot.account, bot.category, bot.symbol)
    if side == "Buy":
        if psn_price - current_price > psn_price * Decimal('0.01'):
            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol,
                side=side,
                orderType="Market",
                qty=get_quantity_from_price(bot.qty, current_price),
            )
            return True
        else:
            return False

    if side == "Sell":
        if current_price - psn_price > psn_price * Decimal('0.01'):
            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol,
                side=side,
                orderType="Market",
                qty=get_quantity_from_price(bot.qty, current_price),
            )
            return True
        else:
            return False
