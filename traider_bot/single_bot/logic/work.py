import math
import time
from decimal import Decimal

from api_test.api_v5_bybit import switch_position_mode, set_leverage, cancel_all, get_current_price
from bots.general_functions import count_decimal_places, custom_logging, clear_data_bot
from bots.models import Take, AvgOrder, Set0Psn, OppositePosition
from bots.SetZeroPsn.logic.need_s0p_start_check import need_set0psn_start_check
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
    set0psn_obj = Set0Psn.objects.filter(bot=bot).first()
    opp_obj = OppositePosition.objects.filter(bot=bot).first()

    new_cycle = True
    if not is_ts_bot:
        tg = TelegramAccount.objects.filter(owner=bot.owner).first()
        if tg:
            chat_id = tg.chat_id
            send_telegram_message(chat_id, message=f'Bot {bot.pk} - {bot} started work')
        switch_position_mode(bot)
        set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)
    fraction_length = int(count_decimal_places(Decimal(bot.symbol.minOrderQty)))
    round_number = int(bot.symbol.priceScale)

    # START CYCLE
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
            psn, psn_qty, psn_side, psn_price, first_cycle, avg_order = entry_position(bot, takes, position_idx)
            '''-------------------------------------------------------------------------------------------'''

            if set0psn_obj and set0psn_obj.set0psn:
                if need_set0psn_start_check(bot, psn):
                    lock.acquire()
                    continue

            if opp_obj and opp_obj.activate_opp:
                if Decimal(psn['unrealisedPnl']) <= Decimal(opp_obj.limit_pnl_loss_opp):
                    current_price_opp = get_current_price(bot.account, bot.category, bot.symbol)
                    side_opp = 'Buy' if psn['positionIdx'] == 2 else 'Sell'
                    qty_opp = Decimal(psn['size']) * Decimal(opp_obj.psn_qty_percent_opp) / 100
                    margin_opp = qty_opp * current_price_opp / bot.isLeverage
                    if margin_opp > Decimal(opp_obj.max_margin_opp):
                        raise Exception('Ошибка при попытке открыть обратную позицию. Превышен лимит маржи.')
                    else:
                        Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side=side_opp,
                            orderType='Market',
                            qty=qty_opp,
                        )
                        cancel_all(bot.account, bot.category, bot.symbol)
                        raise Exception('Open reverse position')

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
                elif avg_order == 'MARGIN LIMIT!':
                    avg_order = AvgOrder.objects.create(bot=bot, order_link_id='margin-limit')
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
        custom_logging(bot, f'Error {e}')
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
            send_telegram_message(chat_id, message=f'Bot {bot.pk} - {bot} finished work')
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


def append_thread_or_check_duplicate(bot_id, is_ts_bot=False):
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
            # raise Exception("Duplicate bot")
            pass
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
    custom_logging(bot, f'bot finished cycle. P&L: {bot.pnl}')
    tg = TelegramAccount.objects.filter(owner=bot.owner).first()
    if tg:
        chat_id = tg.chat_id
        send_telegram_message(chat_id, bot, f'bot finished work. P&L: {bot.pnl}')

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
        clear_data_bot(bot)
        custom_logging(bot, 'New cycle start')
        return True


def check_takes_is_filled(bot, takes):
    pass
    # for take in takes:
    #     if not take.is_filled:
    #         take_status = take_status_check(bot, take)
    #         if take_status:
    #             take.is_filled = True
    #             custom_logging(bot, f'take_{take.take_number} is filled.')
    # Take.objects.bulk_update(takes, ['is_filled'])