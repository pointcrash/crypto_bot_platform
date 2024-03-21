import time
from decimal import Decimal

import os
import django

from bots.bb_set_takes import set_takes
from bots.hedge.logic.entry import set_entry_point_by_market_for_hedge
from bots.models import IsTSStart
from bots.terminate_bot_logic import terminate_thread
from single_bot.logic.global_variables import lock, global_list_bot_id, global_list_threads
from single_bot.logic.work import bot_work_logic
from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from api.api_v5_bybit import get_order_status, get_pnl, set_leverage, switch_position_mode, get_list, get_qty, \
    get_position_price, get_current_price
from bots.bot_logic import count_decimal_places, custom_logging, get_quantity_from_price, create_bb_and_avg_obj
from orders.models import Order


def set_takes_for_hedge_grid_bot(bot):
    bot_id = bot.pk
    flag = False
    first_start = True

    lock.acquire()
    try:
        if bot_id not in global_list_bot_id:
            global_list_bot_id.add(bot_id)
        else:
            global_list_bot_id.remove(bot_id)
            bot.is_active = False
            bot.save()
            raise Exception("Duplicate bot")
    finally:
        lock.release()

    tg = TelegramAccount.objects.filter(owner=bot.owner).first()
    if tg:
        chat_id = tg.chat_id
        send_telegram_message(chat_id, f'Bot {bot.pk} - {bot} started work')

    switch_position_mode(bot)
    set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)
    tp_list = set_entry_point_by_market_for_hedge(bot)

    start_time = int(time.time()) * 1000
    start_pnl_list = get_pnl(bot.account, bot.category, bot.symbol.name, start_time)
    total_pnl = 0
    ml0 = 0
    ml1 = 0

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()

            if flag:
                if bot.work_model == 'bb':
                    IsTSStart.objects.create(bot=bot, TS=True)
                    set_takes(bot)

                elif bot.work_model == 'grid':
                    IsTSStart.objects.create(bot=bot, TS=True)
                    bot_work_logic(bot)

                else:
                    raise Exception('Ошибка при переходе в односторонний режим')
                break

            if not first_start:
                flag1 = False
                waiting_time = bot.time_sleep
                seconds = 1
                while seconds < waiting_time:
                    lock.acquire()
                    try:
                        if bot_id not in global_list_bot_id:
                            flag1 = True
                            seconds = waiting_time
                    finally:
                        if lock.locked():
                            lock.release()
                    if seconds < waiting_time:
                        time.sleep(2)
                        seconds += 2
                if flag1:
                    lock.acquire()
                    continue

            symbol_list, i = None, 0
            while not symbol_list and i < 4:
                symbol_list = get_list(bot.account, bot.category, bot.symbol)
                i += 1
                time.sleep(1)
            price_list = get_position_price(symbol_list)
            qty_list = get_qty(symbol_list)

            new_pnl_list = get_pnl(bot.account, bot.category, bot.symbol.name, start_time)
            if start_pnl_list != new_pnl_list:
                total_pnl += Decimal(new_pnl_list[0]["closedPnl"])
                custom_logging(bot, f'TP IS SUCCESS. Side: {new_pnl_list[0]["side"]} PNL: {round(Decimal(new_pnl_list[0]["closedPnl"]), 2)}')
                start_pnl_list = new_pnl_list

            current_price = get_current_price(bot.account, bot.category, bot.symbol)
            if qty_list[0]:
                margin_after_avg = qty_list[0] * price_list[0] / bot.isLeverage * (1 + bot.bb_avg_percent / 100)

                if margin_after_avg > bot.max_margin:
                    if ml0 != 1:
                        custom_logging(bot, f'MARGIN LIMIT -> {bot.max_margin}, margin after avg -> {round(margin_after_avg, 2)}')
                        ml0 = 1
                else:
                    if not qty_list[1]:
                        qty = get_quantity_from_price(qty_list[0] * price_list[0] / bot.isLeverage, current_price,
                                                      bot.symbol.minOrderQty, bot.isLeverage) * bot.bb_avg_percent / 100
                        avg_price = Decimal(qty_list[0] * price_list[0] + qty * current_price) / (qty_list[0] + qty)
                        Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side='Buy',
                            orderType='Market',
                            qty=qty,
                            # takeProfit=str(round(avg_price * (1 + bot.grid_profit_value / 100), round_number)),

                        )
                        custom_logging(bot,
                                f'position AVG. Side: "Buy". Margin: {round(qty_list[0] * price_list[0] / bot.isLeverage * Decimal(1 + bot.bb_avg_percent / 100), 2)} TP: {round(avg_price * Decimal(1 + bot.grid_profit_value / 100), round_number)}')

                        flag = True

            if qty_list[1]:
                margin_after_avg = qty_list[1] * price_list[1] / bot.isLeverage * (1 + bot.bb_avg_percent / 100)

                if margin_after_avg > bot.max_margin:
                    if ml1 != 1:
                        custom_logging(bot, f'MARGIN LIMIT -> {bot.max_margin}, margin after avg -> {margin_after_avg}')
                        ml1 = 1
                else:
                    if not qty_list[0]:
                        qty = get_quantity_from_price(qty_list[1] * price_list[1] / bot.isLeverage, current_price,
                                                      bot.symbol.minOrderQty, bot.isLeverage) * bot.bb_avg_percent / 100
                        avg_price = Decimal(qty_list[1] * price_list[1] + qty * current_price) / (qty_list[1] + qty)
                        Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side='Sell',
                            orderType='Market',
                            qty=qty,
                            # takeProfit=str(round(avg_price * (1 - bot.grid_profit_value / 100), round_number)),

                        )
                        custom_logging(bot,
                                f'position AVG. Side: "Sell". Margin: {round(qty_list[1] * price_list[1] / bot.isLeverage * Decimal(1 + bot.bb_avg_percent / 100), 2)} TP: {round(avg_price * Decimal(1 - bot.grid_profit_value / 100), round_number)}')

                        flag = True
            lock.acquire()
    # except Exception as e:
    #     print(f'Error {e}')
    #     logging(bot, f'Error {e}')
    #     lock.acquire()
    #     try:
    #         if bot_id in global_list_bot_id:
    #             global_list_bot_id.remove(bot_id)
    #             del global_list_threads[bot_id]
    #             bot.is_active = False
    #             bot.save()
    #     finally:
    #         if lock.locked():
    #             lock.release()
    finally:
        tg = TelegramAccount.objects.filter(owner=bot.owner).first()
        if tg:
            chat_id = tg.chat_id
            send_telegram_message(chat_id, f'Bot {bot.pk} - {bot} finished work')
        if lock.locked():
            lock.release()


def take_status_check(bot, orderLinkId):
    if orderLinkId == 'Filled':
        return 'Filled'
    if orderLinkId:
        status = get_order_status(bot.account, bot.category, bot.symbol, orderLinkId)
        if status == 'Filled':
            pnl = round(Decimal(get_pnl(bot.account, bot.category, bot.symbol)[0]["closedPnl"]), 2)
            bot.pnl = bot.pnl + pnl
            custom_logging(bot, f'take filled. P&L: {pnl}')
            return 'Filled'


