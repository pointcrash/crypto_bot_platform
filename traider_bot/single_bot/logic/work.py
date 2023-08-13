import math
import time
from decimal import Decimal

from api_v5 import switch_position_mode, set_leverage, cancel_all
from bots.bot_logic import count_decimal_places, logging, clear_data_bot
from bots.bot_logic_grid import take_status_check
from bots.models import Take, AvgOrder
from orders.models import Order
from single_bot.logic.entry import entry_position
from single_bot.logic.global_variables import global_list_bot_id, lock, global_list_threads
from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message


def bot_work_logic(bot):
    bot_id = bot.pk
    main_price = 0
    p = 0
    is_ts_bot = True if bot.side == 'TS' else False

    position_idx = get_position_idx(bot.side)
    append_thread_or_check_duplicate(bot_id, is_ts_bot)

    new_cycle = True
    if not is_ts_bot:
        tg = TelegramAccount.objects.filter(owner=bot.owner).first()
        if tg:
            chat_id = tg.chat_id
            send_telegram_message(chat_id, f'Bot {bot.pk} - {bot} started work')
        switch_position_mode(bot)
        set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            lock.release()

            takes = get_takes(bot)
            if not new_cycle:
                check_takes_is_filled(bot, takes)

                if all(take.is_filled for take in takes):
                    actions_after_end_cycle(bot)
                    lock.acquire()
                    continue

            takes = get_takes(bot)

            '''Функция открытия позиций, установление точки входа. А так же усредняющая функция'''
            psn_qty, psn_side, psn_price, first_cycle, avg_order = entry_position(bot, takes, position_idx)
            '''-------------------------------------------------------------------------------------------'''

            takes = get_takes(bot)
            main_price, is_back = check_change_psn_price(bot, main_price, psn_price)
            if is_back:
                lock.acquire()
                continue

            if first_cycle and new_cycle is False:
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

            if not first_cycle or new_cycle is True:
                new_cycle = False
                cancel_all(bot.account, bot.category, bot.symbol)

                if type(avg_order) == Order:
                    avg_order.save()
                    avg_order = AvgOrder.objects.create(bot=bot, order_link_id=avg_order.orderLinkId)
                else:
                    p += 1
                    if p > 5:
                        raise Exception("None-type object in AVG_ORDER")

                side = "Buy" if psn_side == "Sell" else "Sell"
                qty = Decimal(
                    math.floor((psn_qty / bot.grid_take_count) * 10 ** fraction_length) / 10 ** fraction_length)
                oli_list = []

                for i, take in enumerate(takes, start=1):
                    if side == "Buy":
                        price = round(psn_price - psn_price * bot.grid_profit_value * i / 100, round_number)
                    elif side == "Sell":
                        price = round(psn_price + psn_price * bot.grid_profit_value * i / 100, round_number)

                    if not take.is_filled:
                        if i == bot.grid_take_count:
                            order = Order.objects.create(
                                bot=bot,
                                category=bot.category,
                                symbol=bot.symbol.name,
                                side=side,
                                orderType='Limit',
                                qty=round(psn_qty, round_number),
                                price=price,
                                is_take=True,
                            )
                            oli_list.append(order.orderLinkId)

                        else:
                            order = Order.objects.create(
                                bot=bot,
                                category=bot.category,
                                symbol=bot.symbol.name,
                                side=side,
                                orderType='Limit',
                                qty=round(qty, round_number),
                                price=price,
                                is_take=True,
                            )

                            oli_list.append(order.orderLinkId)

                            psn_qty = psn_qty - qty

                for take, oli in zip(takes, oli_list):
                    take.order_link_id = oli
                Take.objects.bulk_update(takes, ['order_link_id'])

            lock.acquire()
    except Exception as e:
        print(f'Error {e}')
        logging(bot, f'Error {e}')
        lock.acquire()
        try:
            if bot_id in global_list_bot_id:
                global_list_bot_id.remove(bot_id)
                del global_list_threads[bot_id]
                bot.is_active = False
                bot.save()
        finally:
            if lock.locked():
                lock.release()
    finally:
        tg = TelegramAccount.objects.filter(owner=bot.owner).first()
        if tg:
            chat_id = tg.chat_id
            send_telegram_message(chat_id, f'Bot {bot.pk} - {bot} finished work')
        if lock.locked():
            lock.release()


def get_takes(bot):
    takes = Take.objects.filter(bot=bot)

    if not takes:
        takes_to_create = [
            Take(bot=bot, take_number=i + 1) for i in range(bot.grid_take_count)
        ]
        Take.objects.bulk_create(takes_to_create)
        return Take.objects.filter(bot=bot)
    else:
        return takes


def get_position_idx(side):
    if side == 'FB' or side == 'TS':
        position_idx = None
    else:
        position_idx = 0 if side == 'Buy' else 1

    return position_idx


def append_thread_or_check_duplicate(bot_id, is_ts_bot):
    lock.acquire()
    try:
        if bot_id not in global_list_bot_id:
            # print('Добавил бота в список')
            global_list_bot_id.add(bot_id)
            # print(global_list_bot_id, 333333333)
        elif is_ts_bot:
            # print('sdgdfsgdfgd', 333333333)
            pass
        else:
            raise Exception("Duplicate bot")
    finally:
        if lock.locked():
            lock.release()


def check_change_psn_price(bot, main_price, psn_price):
    is_back = False
    if main_price != psn_price:
        main_price = psn_price
        avg_order = AvgOrder.objects.filter(bot=bot).first()
        if avg_order:
            avg_order.delete()
            is_back = True
    return main_price, is_back


def actions_after_end_cycle(bot):
    bot_id = bot.pk
    logging(bot, f'bot finished cycle. P&L: {bot.pnl}')
    if not bot.repeat:
        lock.acquire()
        try:
            global_list_bot_id.remove(bot_id)
            bot.is_active = False
            bot.save()
            if bot_id not in global_list_bot_id:
                del global_list_threads[bot_id]
                cancel_all(bot.account, bot.category, bot.symbol)
        finally:
            if lock.locked():
                lock.release()
        return False
    else:
        cancel_all(bot.account, bot.category, bot.symbol)
        # takes = get_takes(bot)
        # avg_order = AvgOrder.objects.filter(bot=bot).first()
        # for take in takes:
        #     take.order_link_id = ''
        #     take.is_filled = False
        # Take.objects.bulk_update(takes, ['order_link_id', 'is_filled'])
        # avg_order.delete()
        clear_data_bot(bot)
        logging(bot, 'New cycle start')
        return True


def check_takes_is_filled(bot, takes):
    for take in takes:
        if not take.is_filled:
            take_status = take_status_check(bot, take)
            if take_status:
                take.is_filled = take_status
                logging(bot, f'take_{take.take_number} is filled.')
    Take.objects.bulk_update(takes, ['is_filled'])