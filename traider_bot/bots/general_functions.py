from datetime import datetime, timedelta
import time
from decimal import Decimal, ROUND_DOWN
from django.core.cache import cache

import os
import django
import pytz

from api_2.api_aggregator import get_exchange_information, get_position_inform, get_open_orders
from api_2.formattres import order_formatters
from single_bot.logic.global_variables import lock, global_list_bot_id, global_list_threads

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
# django.setup()

from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message
from timezone.models import TimeZone
from main.models import ActiveBot, ExchangeService, Account
from bots.models import Symbol, Log, UserBotLog, BotModel
from api_test.api_v5_bybit import cancel_all, get_qty, get_list, get_side, get_position_price, \
    get_symbol_set, get_order_status, get_pnl, get_order_leaves_qty, \
    get_order_created_time


def get_quantity_from_price(qty_USDT, price, minOrderQty, leverage):
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
    pass


def set_buy_entry_point(bot, bl):
    pass


def set_sell_entry_point(bot, tl):
    pass


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
                psn = symbol_list[position_idx]
                psn_qty = get_qty(symbol_list)[position_idx]
                psn_side = get_side(symbol_list)[position_idx]
                psn_price = get_position_price(symbol_list)[position_idx]

                if entry_order_status_check(bot):
                    custom_logging(bot, f'position opened. Margin: {psn_qty * psn_price / bot.isLeverage}')
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
                            custom_logging(bot,
                                    f'average. New margin: {get_qty(symbol_list)[position_idx] * get_position_price(symbol_list)[position_idx] / bot.isLeverage}')
                            first_cycle = False
                            if bot.take1:
                                bot.take1 = ''
                                bot.save()
                            lock.acquire()
                            continue
                return psn, psn_qty, psn_side, psn_price, first_cycle

            if take2_status_check(bot):
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


def get_update_symbols_for_bybit():
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
            coin.qtyStep = symbol[10]
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
                qtyStep=symbol[10],
            )


def get_update_symbols_for_binance():
    symbol_set = get_exchange_information()
    service = ExchangeService.objects.filter(name='Binance').first()
    if not service:
        return
    for symbol_name in symbol_set:
        coin = Symbol.objects.filter(name=symbol_name, service=service).first()
        if coin:
            coin.priceScale = symbol_set[symbol_name]['priceScale']
            coin.maxLeverage = symbol_set[symbol_name]['maxLeverage']
            coin.minPrice = symbol_set[symbol_name]['minPrice']
            coin.maxPrice = symbol_set[symbol_name]['maxPrice']
            coin.minOrderQty = symbol_set[symbol_name]['minQty']
            coin.maxOrderQty = symbol_set[symbol_name]['maxQty']
            coin.tickSize = symbol_set[symbol_name]['priceTickSize']
            coin.qtyStep = symbol_set[symbol_name]['stepQtySize']
            coin.save()
        else:
            Symbol.objects.create(
                name=symbol_name,
                service=service,
                priceScale=symbol_set[symbol_name]['priceScale'],
                maxLeverage=symbol_set[symbol_name]['maxLeverage'],
                minPrice=symbol_set[symbol_name]['minPrice'],
                maxPrice=symbol_set[symbol_name]['maxPrice'],
                minOrderQty=symbol_set[symbol_name]['minQty'],
                maxOrderQty=symbol_set[symbol_name]['maxQty'],
                tickSize=symbol_set[symbol_name]['priceTickSize'],
                qtyStep=symbol_set[symbol_name]['stepQtySize'],
            )


def all_symbols_update():
    for i in range(2):
        if i == 0:
            service = ExchangeService.objects.filter(name='ByBit').first()
            account = Account.objects.filter(name='RomanByBitMainnet', service=service).first()
        else:
            service = ExchangeService.objects.filter(name='Binance').first()
            account = Account.objects.filter(name='RomanBinanceMainnet', service=service).first()

        symbol_set = get_exchange_information(account, service.name)
        if not service:
            return
        for symbol_name in symbol_set:
            coin = Symbol.objects.filter(name=symbol_name, service=service).first()
            symbol_data = symbol_set[symbol_name]
            if coin:
                coin.priceScale = symbol_data['priceScale']
                coin.maxLeverage = symbol_data['maxLeverage']
                coin.minPrice = symbol_data['minPrice']
                coin.maxPrice = symbol_data['maxPrice']
                coin.minOrderQty = symbol_data['minQty']
                coin.maxOrderQty = symbol_data['maxQty']
                coin.tickSize = symbol_data['priceTickSize']
                coin.qtyStep = symbol_data['stepQtySize']
                coin.min_notional = symbol_data['minNotional']
                coin.save()
            else:
                Symbol.objects.create(
                    name=symbol_name,
                    service=service,
                    priceScale=symbol_data['priceScale'],
                    maxLeverage=symbol_data['maxLeverage'],
                    minPrice=symbol_data['minPrice'],
                    maxPrice=symbol_data['maxPrice'],
                    minOrderQty=symbol_data['minQty'],
                    maxOrderQty=symbol_data['maxQty'],
                    tickSize=symbol_data['priceTickSize'],
                    qtyStep=symbol_data['stepQtySize'],
                    min_notional=symbol_data['minNotional'],
                )


def clear_symbols():
    symbols = Symbol.objects.all()
    for symbol in symbols:
        if not symbol.service:
            symbol.delete()


def count_decimal_places(number):
    decimal_tuple = number.as_tuple()
    decimal_places = -decimal_tuple.exponent
    return decimal_places


def custom_logging(bot, text):
    user = bot.owner
    timezone = TimeZone.objects.filter(users=user).first()
    gmt0 = pytz.timezone('GMT')
    date = datetime.now(gmt0).replace(microsecond=0)
    bot_info = f'Bot {bot.pk} {bot.symbol.name}'
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

            custom_logging(bot, f'Позиция докупилась на {entry_order_by_amount}')

    if bot.entry_order_sell:
        # logging(bot, f'entry_order_sell_id - {bot.entry_order_sell}')
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.entry_order_sell)
        # logging(bot, f'status - {status}')
        if status == 'PartiallyFilled':
            entry_order_sell_amount = Decimal(
                get_order_leaves_qty(bot.account, bot.category, bot.symbol, bot.entry_order_sell))
            # logging(bot, f'entry_order_sell_amount - {entry_order_sell_amount}')
            custom_logging(bot, f'Позиция докупилась на {entry_order_sell_amount}')


def take1_status_check(bot):
    if bot.take1 == 'Filled':
        return True
    if bot.take1:
        status = get_order_status(bot.account, bot.category, bot.symbol, bot.take1)
        if status == 'Filled':
            pnl = get_pnl(bot.account, bot.category, bot.symbol)[0]['closedPnl']
            bot.pnl = bot.pnl + round(Decimal(pnl), 2)
            custom_logging(bot, f'take1 filled. P&L: {pnl}')
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
        custom_logging(bot, f'take2 filled. P&L: {pnl}')
        bot.take2 = 'Filled'
        bot.save()
        return True


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


def func_get_symbol_list(bot):
    symbol_list, i = None, 0
    while not symbol_list and i < 4:
        symbol_list = get_list(bot.account, 'linear', bot.symbol)
        i += 1
        time.sleep(1)
    return symbol_list


def bin_order_buy_in_addition(bot, side):
    status = get_order_status(bot.account, bot.category, bot.symbol, bot.bin_order_id)
    if status == 'PartiallyFilled':
        entry_order_by_amount = Decimal(
            get_order_leaves_qty(bot.account, bot.category, bot.symbol, bot.bin_order_id))

        custom_logging(bot, 'BIN-order addition')
        return True

    elif status == 'Filled':
        custom_logging(bot, 'BIN-order is filled')
        return True


def lock_release():
    if lock.locked():
        lock.release()


def exit_by_exception(bot):
    bot_id = bot.pk
    if is_bot_active(bot_id):
        ActiveBot.objects.filter(bot_id=bot_id).delete()

    if bot_id in global_list_bot_id:
        global_list_bot_id.remove(bot_id)
        del global_list_threads[bot_id]
        bot.is_active = False
        bot.save()


def is_bot_active(bot_id):
    return ActiveBot.objects.filter(bot_id=bot_id).exists()


def clear_cache_bot_data(bot_id):
    bot_cache_keys = [key for key in cache.keys(f'bot{bot_id}*')]
    for key in bot_cache_keys:
        cache.delete(key)


def get_cur_positions_and_orders_info(bot):
    positions = get_position_inform(bot)
    for position in positions:
        position['leverage'] = bot.leverage
        position['cost'] = round(float(position['qty']) * float(position['entryPrice']), 2)
        position['margin'] = round(position['cost'] / position['leverage'], 2)
        if position['margin']:
            position['roi'] = round(float(position['unrealisedPnl']) / position['margin'] * 100, 2)
        else:
            position['roi'] = 0

    raw_orders = get_open_orders(bot)
    orders = [order_formatters(order) for order in raw_orders] if raw_orders else None
    return positions, orders


def send_telegram_notice(account, message):
    telegram_account = TelegramAccount.objects.filter(owner=account.owner).first()
    if telegram_account:
        send_telegram_message(telegram_account.chat_id, message=message)


def custom_user_bot_logging(bot, content):
    user = bot.owner
    timezone = TimeZone.objects.filter(users=user).first()
    gmt0 = pytz.timezone('GMT')
    date = datetime.now(gmt0).replace(microsecond=0)
    bot_info = f'Bot {bot.pk} {bot.symbol.name}'
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
    UserBotLog.objects.create(bot=bot, content=f'{bot_info} {content}', time=f'{in_time} (GMT {str_gmt})')


def update_bots_conn_status(bot, new_status):
    BotModel.objects.filter(pk=bot.pk).update(conn_status=new_status)


def update_bots_is_active(bot, new_status):
    BotModel.objects.filter(pk=bot.pk).update(is_active=new_status)


def update_bots_forcibly_stopped(bot, forcibly_stopped):
    BotModel.objects.filter(pk=bot.pk).update(forcibly_stopped=forcibly_stopped)

