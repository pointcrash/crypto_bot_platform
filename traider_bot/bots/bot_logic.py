from datetime import datetime
import time
from decimal import Decimal, ROUND_DOWN

import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from bots.bb_auto_avg import BBAutoAverage
from bots.bb_class import BollingerBands
from bots.models import Symbol, Log
from api_v5 import cancel_all, get_qty, get_list, get_side, get_position_price, get_current_price, \
    get_symbol_set
from orders.models import Order


def get_quantity_from_price(qty_USDT, price, minOrderQty):
    return (Decimal(str(qty_USDT)) / price).quantize(Decimal(minOrderQty), rounding=ROUND_DOWN)


def set_entry_point_by_market(bot):
    order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol.name,
        isLeverage=bot.isLeverage,
        side=bot.side,
        orderType=bot.orderType,
        qty=get_quantity_from_price(bot.qty,
                                    get_current_price(bot.account, bot.category, bot.symbol),
                                    bot.symbol.minOrderQty)
    )


def set_buy_entry_point(bot, bl):
    if bot.is_percent_deviation_from_lines:
        price = bl - bl * bot.deviation_from_lines / 100
    else:
        price = bl - bot.deviation_from_lines

    buy_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol.name,
        isLeverage=bot.isLeverage,
        side="Buy",
        orderType=bot.orderType,
        qty=get_quantity_from_price(bot.qty, bl - Decimal(bot.symbol.minPrice), bot.symbol.minOrderQty),
        price=price,
    )


def set_sell_entry_point(bot, tl):
    if bot.is_percent_deviation_from_lines:
        price = tl + tl * bot.deviation_from_lines / 100
    else:
        price = tl + bot.deviation_from_lines

    sell_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol.name,
        isLeverage=bot.isLeverage,
        side="Sell",
        orderType=bot.orderType,
        qty=get_quantity_from_price(bot.qty, tl + Decimal(bot.symbol.minPrice), bot.symbol.minOrderQty),
        price=price,
    )


def set_entry_point(bot, tl, bl):
    if bot.side == "Buy":
        set_buy_entry_point(bot, bl)
    elif bot.side == "Sell":
        set_sell_entry_point(bot, tl)
    elif bot.side == "Auto":
        set_buy_entry_point(bot, bl)
        set_sell_entry_point(bot, tl)


def calculation_entry_point(bot, bb_obj, bb_avg_obj):
    first_cycle = True

    while True:
        symbol_list = get_list(bot.account, bot.category, bot.symbol)

        if get_qty(symbol_list):
            psn_qty = get_qty(symbol_list)
            psn_side = get_side(symbol_list)
            psn_price = get_position_price(symbol_list)
            # logging(bot, f'open position margin: {psn_qty*psn_price}')

            bb_avg_obj.psn_price = psn_price
            bb_avg_obj.psn_side = psn_side
            bb_avg_obj.psn_qty = psn_qty

            if bot.auto_avg:
                if bot.work_model == "grid" and to_avg_by_grid(bot, psn_side, psn_price, psn_qty):
                    first_cycle = False
                    continue
                elif bot.work_model == "bb" and bb_avg_obj is not None:
                    if bb_avg_obj.auto_avg():
                        symbol_list = get_list(bot.account, bot.category, bot.symbol)
                        logging(bot, f'average. New margin: {get_qty(symbol_list)*get_position_price(symbol_list)}')
                        first_cycle = False
                        continue

            return psn_qty, psn_side, psn_price, first_cycle

        if bot.orderType == "Market":
            set_entry_point_by_market(bot)
            first_cycle = False
            continue

        tl = bb_obj.tl
        bl = bb_obj.bl

        if not first_cycle:
            time.sleep(10)

        if first_cycle or tl != bb_obj.tl or bl != bb_obj.bl:
            cancel_all(bot.account, bot.category, bot.symbol)
            set_entry_point(bot, tl, bl)

        first_cycle = False


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


def create_bb_and_avg_obj(bot):
    symbol_list = get_list(bot.account, bot.category, bot.symbol)
    psn_qty = get_qty(symbol_list)
    psn_side = get_side(symbol_list)
    psn_price = get_position_price(symbol_list)

    if bot.work_model == 'grid' and bot.orderType == 'Market':
        bb_obj = None
    else:
        bb_obj = BollingerBands(account=bot.account, category=bot.category, symbol_name=bot.symbol.name,
                                symbol_priceScale=bot.symbol.priceScale, interval=bot.interval,
                                qty_cline=bot.qty_kline, d=bot.d)

    if bot.work_model != 'grid' and bot.auto_avg:
        bb_avg_obj = BBAutoAverage(bot=bot, psn_price=psn_price, psn_side=psn_side, psn_qty=psn_qty,
                                   bb_obj=bb_obj)
    else:
        bb_avg_obj = None

    return bb_obj, bb_avg_obj


def to_avg_by_grid(bot, side, psn_price, psn_qty):
    current_price = get_current_price(bot.account, bot.category, bot.symbol)
    psn_currency_amount = psn_price * psn_qty
    avg_currency_amount = psn_currency_amount * bot.bb_avg_percent / 100

    if psn_currency_amount + avg_currency_amount <= bot.max_margin:
        if side == "Buy":
            if psn_price - current_price > psn_price * bot.grid_avg_value / 100:
                order = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    isLeverage=bot.isLeverage,
                    side=side,
                    orderType="Market",
                    qty=get_quantity_from_price(avg_currency_amount, current_price, bot.symbol.minOrderQty),
                )
                return True
            else:
                return False

        if side == "Sell":
            if current_price - psn_price > psn_price * bot.grid_avg_value / 100:
                order = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    isLeverage=bot.isLeverage,
                    side=side,
                    orderType="Market",
                    qty=get_quantity_from_price(avg_currency_amount, current_price, bot.symbol.minOrderQty),
                )
                return True
            else:
                return False
    return False


def logging(bot, text):
    bot_info = f'Bot {bot.pk} {bot.symbol.name} {bot.side} {bot.interval}'
    date = datetime.now().replace(microsecond=0)
    in_time = f'{date.time()} {date.date()}'
    Log.objects.create(bot=bot, content=f'{bot_info} {text} {in_time}')

# print(get_symbol_set())