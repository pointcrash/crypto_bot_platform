import multiprocessing
from datetime import datetime
import time
from decimal import Decimal, ROUND_DOWN

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from bots.bb_auto_avg import BBAutoAverage
from bots.bb_class import BollingerBands
from bots.models import Symbol, Log, AvgOrder
from api_v5 import cancel_all, get_qty, get_list, get_side, get_position_price, get_current_price, \
    get_symbol_set, get_order_status, get_pnl
from orders.models import Order


def get_quantity_from_price(qty_USDT, price, minOrderQty, leverage):
    return (Decimal(str(qty_USDT * leverage)) / price).quantize(Decimal(minOrderQty), rounding=ROUND_DOWN)


def set_entry_point_by_market(bot):
    order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol.name,
        side=bot.side,
        orderType="Market",
        qty=get_quantity_from_price(bot.qty,
                                    get_current_price(bot.account, bot.category, bot.symbol),
                                    bot.symbol.minOrderQty, bot.isLeverage)
    )

    logging(bot, f'create order by market')
    if bot.side == 'Sell':
        bot.entry_order_sell = order.orderLinkId
        bot.save()
    else:
        bot.entry_order_by = order.orderLinkId
        bot.save()


def set_buy_entry_point(bot, bl):
    if bot.is_percent_deviation_from_lines:
        price = bl - bl * bot.deviation_from_lines / 100
    else:
        price = bl - bot.deviation_from_lines

    buy_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol.name,
        side="Buy",
        orderType=bot.orderType,
        qty=get_quantity_from_price(bot.qty, bl - Decimal(bot.symbol.minPrice), bot.symbol.minOrderQty, bot.isLeverage),
        price=price,
    )

    logging(bot, f'create BUY-order. Price: {price}')
    bot.entry_order_by = buy_order.orderLinkId
    bot.save()


def set_sell_entry_point(bot, tl):
    if bot.is_percent_deviation_from_lines:
        price = tl + tl * bot.deviation_from_lines / 100
    else:
        price = tl + bot.deviation_from_lines

    sell_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol.name,
        side="Sell",
        orderType=bot.orderType,
        qty=get_quantity_from_price(bot.qty, tl + Decimal(bot.symbol.minPrice), bot.symbol.minOrderQty, bot.isLeverage),
        price=price,
    )

    logging(bot, f'create SELL-order. Price: {price}')
    bot.entry_order_sell = sell_order.orderLinkId
    bot.save()


def set_entry_point(bot, tl, bl):
    if bot.side == "Buy":
        set_buy_entry_point(bot, bl)
    elif bot.side == "Sell":
        set_sell_entry_point(bot, tl)
    elif bot.side == "FB":
        set_buy_entry_point(bot, bl)
        set_sell_entry_point(bot, tl)


def calculation_entry_point(bot, bb_obj, bb_avg_obj, grid_take_list=None):
    first_cycle = True
    position_idx = 0 if bot.side == 'Buy' else 1

    while True:
        symbol_list = get_list(bot.account, bot.category, bot.symbol)

        if get_qty(symbol_list)[position_idx]:
            psn_qty = get_qty(symbol_list)[position_idx]
            psn_side = get_side(symbol_list)[position_idx]
            psn_price = get_position_price(symbol_list)[position_idx]
            if entry_order_status_check(bot):
                logging(bot, f'position opened. Margin: {psn_qty * psn_price / bot.isLeverage}')

            if bb_avg_obj:
                bb_avg_obj.psn_price = psn_price
                bb_avg_obj.psn_side = psn_side
                bb_avg_obj.psn_qty = psn_qty

            if bot.auto_avg:
                if bot.work_model == "bb" and bb_avg_obj is not None:
                    if bb_avg_obj.auto_avg():
                        symbol_list = get_list(bot.account, bot.category, bot.symbol)
                        logging(bot, f'average. New margin: {get_qty(symbol_list)[position_idx] * get_position_price(symbol_list)[position_idx] / bot.isLeverage}')
                        first_cycle = False
                        if bot.take1:
                            bot.take1 = ''
                            bot.save()
                        continue

            return psn_qty, psn_side, psn_price, first_cycle, grid_take_list

        if bot.orderType == "Market":
            set_entry_point_by_market(bot)
            first_cycle = False
            continue

        tl = bb_obj.tl
        bl = bb_obj.bl

        if not first_cycle:
            time.sleep(bot.time_sleep)

        if first_cycle or tl != bb_obj.tl or bl != bb_obj.bl:
            cancel_all(bot.account, bot.category, bot.symbol)
            set_entry_point(bot, tl, bl)

        first_cycle = False


def get_update_symbols():
    symbol_set = get_symbol_set()
    for symbol in symbol_set:
        try:
            coin = Symbol.objects.get(name=symbol[0])
        except Symbol.DoesNotExist:
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


def create_bb_and_avg_obj(bot, position_idx):
    if bot.work_model == 'bb':
        symbol_list = get_list(bot.account, bot.category, bot.symbol)
        psn_qty = get_qty(symbol_list)[position_idx]
        psn_side = get_side(symbol_list)[position_idx]
        psn_price = get_position_price(symbol_list)[position_idx]

    if bot.work_model == 'grid' and bot.orderType == 'Market':
        bb_obj = None
    else:
        bb_obj = BollingerBands(account=bot.account, category=bot.category, symbol_name=bot.symbol.name,
                                symbol_priceScale=bot.symbol.priceScale, interval=bot.interval,
                                qty_cline=bot.qty_kline, d=bot.d)

    if bot.work_model == 'bb' and bot.auto_avg:
        bb_avg_obj = BBAutoAverage(bot=bot, psn_price=psn_price, psn_side=psn_side, psn_qty=psn_qty,
                                   bb_obj=bb_obj)
    else:
        bb_avg_obj = None

    return bb_obj, bb_avg_obj


def logging(bot, text):
    bot_info = f'Bot {bot.pk} {bot.symbol.name} {bot.side} {bot.interval}'
    date = datetime.now().replace(microsecond=0)
    in_time = f'{date.time()} {date.date()}'
    Log.objects.create(bot=bot, content=f'{bot_info} {text} {in_time}')


def entry_order_status_check(bot):
    if bot.entry_order_by:
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.entry_order_by)
        if status == 'Filled':
            bot.entry_order_by = ''
            bot.save()
            return True

    if bot.entry_order_sell:
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.entry_order_sell)
        if status == 'Filled':
            bot.entry_order_sell = ''
            bot.save()
            return True


def take1_status_check(bot):
    if bot.take1 == 'Filled':
        return True
    if bot.take1:
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.take1)
        if status == 'Filled':
            pnl = get_pnl(bot.account, bot.category, bot.symbol)
            bot.pnl += Decimal(pnl)
            logging(bot, f'take1 filled. P&L: {pnl}')
            bot.take1 = 'Filled'
            bot.save()
            return True


def take2_status_check(bot):
    if bot.take2:
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.take2)
        if status == 'Filled':
            pnl = get_pnl(bot.account, bot.category, bot.symbol)
            bot.pnl += Decimal(pnl)
            logging(bot, f'take2 filled. P&L: {pnl}')
            bot.take2 = ''
            bot.save()
            return True


# get_symbol_set()

