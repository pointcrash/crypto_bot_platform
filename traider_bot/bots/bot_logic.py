from datetime import datetime, timedelta
import time
from decimal import Decimal, ROUND_DOWN

import os
import django
import pytz

from single_bot.logic.global_variables import lock, global_list_bot_id, global_list_threads
from timezone.models import TimeZone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from bots.bb_auto_avg import BBAutoAverage
from bots.bb_class import BollingerBands
from bots.models import Symbol, Log, AvgOrder, Bot, Take, IsTSStart
from api_v5 import cancel_all, get_qty, get_list, get_side, get_position_price, get_current_price, \
    get_symbol_set, get_order_status, get_pnl, get_order_leaves_qty, \
    get_order_created_time
from orders.models import Order


def get_quantity_from_price(qty_USDT, price, minOrderQty, leverage):
    # print('qty_USDT', qty_USDT, type(qty_USDT))
    # print('price', price, type(price))
    # print('minOrderQty', minOrderQty)
    # print('leverage', leverage, type(leverage))
    return (Decimal(str(qty_USDT * leverage)) / price).quantize(Decimal(minOrderQty), rounding=ROUND_DOWN)


def get_position_idx_by_range(symbol_list):
    for i in range(2):
        if get_qty(symbol_list)[i]:
            return i
    return None


def get_position_idx(side):
    if side == 'FB' or side == 'TS':
        position_idx = None
    else:
        position_idx = 0 if side == 'Buy' else 1

    return position_idx


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
    round_number = int(bot.symbol.priceScale)
    if bot.is_percent_deviation_from_lines:
        price = round(bl - bl * bot.deviation_from_lines / 100, round_number)
    else:
        price = round(bl - bot.deviation_from_lines, round_number)

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
    round_number = int(bot.symbol.priceScale)
    if bot.is_percent_deviation_from_lines:
        price = round(tl + tl * bot.deviation_from_lines / 100, round_number)
    else:
        price = round(tl + bot.deviation_from_lines, round_number)

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


def calculation_entry_point(bot, bb_obj, bb_avg_obj):
    bot_id = bot.pk
    first_cycle = True
    position_idx = get_position_idx(bot.side)

    tl = bb_obj.tl
    bl = bb_obj.bl

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()

            symbol_list = func_get_symbol_list(bot)

            if position_idx is None:
                position_idx = get_position_idx_by_range(symbol_list)

            if position_idx is not None and get_qty(symbol_list)[position_idx]:
                psn_qty = get_qty(symbol_list)[position_idx]
                psn_side = get_side(symbol_list)[position_idx]
                psn_price = get_position_price(symbol_list)[position_idx]

                if entry_order_status_check(bot):
                    logging(bot, f'position opened. Margin: {psn_qty * psn_price / bot.isLeverage}')
                else:
                    entry_order_buy_in_addition(bot)
                    symbol_list = func_get_symbol_list(bot)
                    psn_qty = get_qty(symbol_list)[position_idx]
                    psn_side = get_side(symbol_list)[position_idx]
                    psn_price = get_position_price(symbol_list)[position_idx]

                bot.entry_order_by = ''
                bot.entry_order_sell = ''
                bot.save()

                if bb_avg_obj:
                    bb_avg_obj.psn_price = psn_price
                    bb_avg_obj.psn_side = psn_side
                    bb_avg_obj.psn_qty = psn_qty

                if bot.auto_avg:
                    if bot.work_model == "bb" and bb_avg_obj is not None:
                        if bb_avg_obj.auto_avg():
                            symbol_list, i = None, 0
                            while not symbol_list and i < 4:
                                symbol_list = get_list(bot.account, bot.category, bot.symbol)
                                i += 1
                                time.sleep(1)
                            logging(bot,
                                    f'average. New margin: {get_qty(symbol_list)[position_idx] * get_position_price(symbol_list)[position_idx] / bot.isLeverage}')
                            first_cycle = False
                            if bot.take1:
                                bot.take1 = ''
                                bot.save()
                            lock.acquire()
                            continue
                return psn_qty, psn_side, psn_price, first_cycle

            if take2_status_check(bot):
                actions_after_end_cycle(bot)
                lock.acquire()
                continue

            if bot.orderType == "Market":
                set_entry_point_by_market(bot)
                first_cycle = False
                lock.acquire()
                continue

            if bot.side == 'FB':
                if not all(order_placement_verification(bot, order_id) for order_id in
                           [bot.entry_order_by, bot.entry_order_sell]) or not all(
                            check_order_placement_time(bot, order_id) for order_id in
                            [bot.entry_order_by, bot.entry_order_sell]):
                    bot.entry_order_by, bot.entry_order_sell = '', ''
                    bot.save()
                    first_cycle = True
            elif bot.side == 'Sell':
                order_id = bot.entry_order_sell
                if not order_placement_verification(bot, order_id) or not check_order_placement_time(bot, order_id):
                    bot.entry_order_sell = ''
                    bot.save()
                    first_cycle = True
            elif bot.side == 'Buy':
                order_id = bot.entry_order_by
                if not order_placement_verification(bot, order_id) or not check_order_placement_time(bot, order_id):
                    bot.entry_order_by = ''
                    bot.save()
                    first_cycle = True

            if not first_cycle:
                flag = False
                waiting_time = bot.time_sleep
                seconds = 1
                while seconds < waiting_time:
                    lock.acquire()
                    try:
                        if bot_id not in global_list_bot_id:
                            flag = True
                            seconds = waiting_time
                    finally:
                        if lock.locked():
                            lock.release()
                    if seconds < waiting_time:
                        time.sleep(2)
                        seconds += 2
                if flag:
                    lock.acquire()
                    continue

            if first_cycle or tl != bb_obj.tl or bl != bb_obj.bl:
                cancel_all(bot.account, bot.category, bot.symbol)
                tl = bb_obj.tl
                bl = bb_obj.bl
                set_entry_point(bot, tl, bl)

            first_cycle = False
            lock.acquire()
    finally:
        if lock.locked():
            lock.release()


def get_update_symbols():
    symbol_set = get_symbol_set()
    for symbol in symbol_set:
        coin = Symbol.objects.filter(name=symbol[0]).first()
        if coin:
            coin.priceScale = symbol[1]
            coin.minLeverage = symbol[2]
            coin.maxLeverage = symbol[3]
            coin.leverageStep = symbol[4]
            coin.minPrice = symbol[5]
            coin.maxPrice = symbol[6]
            coin.minOrderQty = symbol[7]
            coin.maxOrderQty = symbol[8]
            coin.tickSize = symbol[9]
            coin.save()
        else:
            Symbol.objects.create(
                name=symbol[0],
                priceScale=symbol[1],
                minLeverage=symbol[2],
                maxLeverage=symbol[3],
                leverageStep=symbol[4],
                minPrice=symbol[5],
                maxPrice=symbol[6],
                minOrderQty=symbol[7],
                maxOrderQty=symbol[8],
                tickSize=symbol[9],
            )


def count_decimal_places(number):
    decimal_tuple = number.as_tuple()
    decimal_places = -decimal_tuple.exponent
    return decimal_places


def create_bb_and_avg_obj(bot, position_idx=0):
    if bot.work_model == 'grid' and bot.orderType == 'Market':
        bb_obj = None
    else:
        bb_obj = BollingerBands(account=bot.account, category=bot.category, symbol_name=bot.symbol.name,
                                symbol_priceScale=bot.symbol.priceScale, interval=bot.interval,
                                qty_cline=bot.qty_kline, d=bot.d)

    if bot.work_model == 'bb' and bot.auto_avg:
        bb_avg_obj = BBAutoAverage(bot=bot, psn_price=0, psn_side=0, psn_qty=0,
                                   bb_obj=bb_obj)
    else:
        bb_avg_obj = None

    return bb_obj, bb_avg_obj


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

    in_time = f'{date.time()} {date.date()}'
    Log.objects.create(bot=bot, content=f'{bot_info} {text} {in_time} (GMT {str_gmt})')


def entry_order_status_check(bot):
    if bot.entry_order_by:
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.entry_order_by)
        if status == 'Filled':
            return True

    if bot.entry_order_sell:
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.entry_order_sell)
        if status == 'Filled':
            return True


def entry_order_buy_in_addition(bot):
    # logging(bot, f'entry_order_by_id - {bot.entry_order_by}')
    if bot.entry_order_by:
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.entry_order_by)
        # logging(bot, f'status - {status}')
        if status == 'PartiallyFilled':
            entry_order_by_amount = Decimal(
                get_order_leaves_qty(bot.account, bot.category, bot.symbol, bot.entry_order_by))
            # logging(bot, f'entry_order_by_amount - {entry_order_by_amount}')

            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol.name,
                side='Buy',
                orderType="Market",
                qty=entry_order_by_amount
            )
            logging(bot, f'Позиция докупилась на {entry_order_by_amount}')

    if bot.entry_order_sell:
        # logging(bot, f'entry_order_sell_id - {bot.entry_order_sell}')
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.entry_order_sell)
        # logging(bot, f'status - {status}')
        if status == 'PartiallyFilled':
            entry_order_sell_amount = Decimal(
                get_order_leaves_qty(bot.account, bot.category, bot.symbol, bot.entry_order_sell))
            # logging(bot, f'entry_order_sell_amount - {entry_order_sell_amount}')
            order = Order.objects.create(
                bot=bot,
                category=bot.category,
                symbol=bot.symbol.name,
                side='Sell',
                orderType="Market",
                qty=entry_order_sell_amount
            )
            logging(bot, f'Позиция докупилась на {entry_order_sell_amount}')


def take1_status_check(bot):
    if bot.take1 == 'Filled':
        return True
    if bot.take1:
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.take1)
        if status == 'Filled':
            pnl = get_pnl(bot.account, bot.category, bot.symbol)[0]['closedPnl']
            bot.pnl = bot.pnl + round(Decimal(pnl), 2)
            logging(bot, f'take1 filled. P&L: {pnl}')
            bot.take1 = 'Filled'
            bot.save()
            return True


def order_leaves_qty_check(bot, order_id):
    if order_id and order_id != 'Filled':
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.take1)
        if status == 'PartiallyFilled':
            bot.take2_amount = Decimal(get_order_leaves_qty(bot.account, bot.category, bot.symbol, bot.take1))
            bot.save()
            return True


def take2_status_check(bot):
    status = get_order_status(bot.account, bot.category, bot.symbol, bot.take2)
    if status == 'Filled':
        pnl = get_pnl(bot.account, bot.category, bot.symbol)[0]['closedPnl']
        bot.pnl = bot.pnl + round(Decimal(pnl), 2)
        logging(bot, f'take2 filled. P&L: {pnl}')
        bot.take2 = 'Filled'
        bot.save()
        return True


# def bot_stats_clear(bot):
#     bot.take1 = ''
#     bot.take2 = ''
#     bot.entry_order_by = ''
#     bot.entry_order_sell = ''
#     bot.pnl = 0
#     bot.save()


def order_placement_verification(bot, order_id):
    if order_id == 'Filled' or not order_id:
        return True
    status = get_order_status(bot.account, bot.category, bot.symbol, order_id)
    # logging(bot, f'Order- {order_id} status: {status}')
    if status == "Order not found":
        return False
    else:
        return True


def check_order_placement_time(bot, order_id):
    if order_id == 'Filled' or not order_id:
        return True
    order_time_create = get_order_created_time(bot.account, bot.category, bot.symbol, order_id)
    # logging(bot, f'Order- {order_id} time create: {order_time_create}')

    if order_time_create == "Order not found":
        return False
    else:
        order_time_create = datetime.fromtimestamp(int(order_time_create) // 1000)
        current_time = datetime.now()
        time_difference = current_time - order_time_create
        time_difference_in_minutes = time_difference.total_seconds() / 60

        if int(time_difference_in_minutes) <= int(bot.interval):
            return True


def clean_and_return_bot_object(bot_id):
    bot_values_dict = Bot.objects.filter(pk=bot_id).values().first()
    bot = Bot(
        owner_id=bot_values_dict['owner_id'],
        account_id=bot_values_dict['account_id'],
        category=bot_values_dict['category'],
        symbol_id=bot_values_dict['symbol_id'],
        isLeverage=bot_values_dict['isLeverage'],
        side=bot_values_dict['side'],
        orderType=bot_values_dict['orderType'],
        qty=bot_values_dict['qty'],
        margin_type=bot_values_dict['margin_type'],
        qty_kline=bot_values_dict['qty_kline'],
        interval=bot_values_dict['interval'],
        d=bot_values_dict['d'],
        work_model=bot_values_dict['work_model'],
        take_on_ml=bot_values_dict['take_on_ml'],
        take_on_ml_percent=bot_values_dict['take_on_ml_percent'],
        auto_avg=bot_values_dict['auto_avg'],
        bb_avg_percent=bot_values_dict['bb_avg_percent'],
        grid_avg_value=bot_values_dict['grid_avg_value'],
        grid_profit_value=bot_values_dict['grid_profit_value'],
        grid_take_count=bot_values_dict['grid_take_count'],
        is_percent_deviation_from_lines=bot_values_dict['is_percent_deviation_from_lines'],
        deviation_from_lines=bot_values_dict['deviation_from_lines'],
        dfm=bot_values_dict['dfm'],
        chw=bot_values_dict['chw'],
        max_margin=bot_values_dict['max_margin'],
        time_sleep=bot_values_dict['time_sleep'],
        repeat=bot_values_dict['repeat'],
    )

    return bot


def clear_data_bot(bot, clear_data=0):
    from django.db import connections

    bot.entry_order_by = ''
    bot.entry_order_by_amount = None
    bot.entry_order_sell = ''
    bot.entry_order_sell_amount = None
    if bot.take1 != 'Filled' or bot.take2 == 'Filled':
        bot.take1 = ''
    bot.take2 = ''
    bot.take2_amount = None
    bot.bin_order_id = ''

    if clear_data == 0:
        bot.pnl = 0
        avg_order = AvgOrder.objects.filter(bot=bot).first()
        takes = Take.objects.filter(bot=bot)
        if bot.side != 'TS':
            is_ts_start = IsTSStart.objects.filter(bot=bot).first()
            if is_ts_start:
                is_ts_start.delete()
        if takes:
            takes.delete()
        if avg_order:
            avg_order.delete()

    bot.save()
    connections.close_all()


def actions_after_end_cycle(bot):
    bot_id = bot.pk
    logging(bot, f'bot finished work. P&L: {bot.pnl}')
    if not bot.repeat:
        lock.acquire()
        try:
            global_list_bot_id.remove(bot_id)
            bot.is_active = False
            bot.save()
            if bot_id not in global_list_bot_id:
                del global_list_threads[bot_id]
        finally:
            if lock.locked():
                lock.release()
    else:
        clear_data_bot(bot)
        logging(bot, 'Bot start new cycle')


def func_get_symbol_list(bot):
    symbol_list, i = None, 0
    while not symbol_list and i < 4:
        symbol_list = get_list(bot.account, bot.category, bot.symbol)
        i += 1
        time.sleep(1)
    return symbol_list


def bin_order_buy_in_addition(bot, side):
    status = get_order_status(bot.account, bot.category, bot.symbol, bot.bin_order_id)
    if status == 'PartiallyFilled':
        entry_order_by_amount = Decimal(
            get_order_leaves_qty(bot.account, bot.category, bot.symbol, bot.bin_order_id))

        order = Order.objects.create(
            bot=bot,
            category=bot.category,
            symbol=bot.symbol.name,
            side=side,
            orderType="Market",
            qty=entry_order_by_amount
        )
        logging(bot, 'BIN-order addition')
        return True

    elif status == 'Filled':
        logging(bot, 'BIN-order is filled')
        return True

