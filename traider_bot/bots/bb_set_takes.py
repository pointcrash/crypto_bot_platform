import time

from decimal import Decimal

from api_v5 import cancel_all, switch_position_mode, set_leverage, get_current_price, get_list
from bots.bot_logic import calculation_entry_point, take1_status_check, logging, \
    take2_status_check, create_bb_and_avg_obj, order_leaves_qty_check, order_placement_verification, \
    check_order_placement_time, actions_after_end_cycle, bin_order_buy_in_addition
from bots.models import Set0Psn
from bots.set_zero_psn.logic.need_s0p_start_check import need_set0psn_start_check
from orders.models import Order
from single_bot.logic.global_variables import lock, global_list_bot_id, global_list_threads
from single_bot.logic.work import append_thread_or_check_duplicate
from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message


def set_takes(bot):
    bot_id = bot.pk
    first_start = True
    round_number = int(bot.symbol.priceScale)
    is_ts_bot = True if bot.side == 'TS' else False
    append_thread_or_check_duplicate(bot_id, is_ts_bot)
    set0psn_obj = Set0Psn.objects.filter(bot=bot).first()

    if not is_ts_bot:
        tg = TelegramAccount.objects.filter(owner=bot.owner).first()
        if tg:
            chat_id = tg.chat_id
            send_telegram_message(chat_id, f'Bot {bot.pk} - {bot} started work')
        switch_position_mode(bot)
        set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)

    bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)

    tl = bb_obj.tl
    bl = bb_obj.bl

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()

            '''  Функция установки точек входа и усреднения  '''
            try:
                psn, psn_qty, psn_side, psn_price, first_cycle = calculation_entry_point(bot=bot, bb_obj=bb_obj, bb_avg_obj=bb_avg_obj)
            except Exception as e:
                if isinstance(e, TypeError):
                    lock.acquire()
                    continue
                else:
                    raise ValueError(f'Ошибка в блоке calculation_entry_point: {e}')

            if set0psn_obj and set0psn_obj.set0psn:
                if need_set0psn_start_check(bot, psn):
                    lock.acquire()
                    continue

            if first_start:
                first_cycle = False
                first_start = False

            if bot.take_on_ml:
                if not all(order_placement_verification(bot, order_id) for order_id in
                           [bot.take1, bot.take2]) or not all(check_order_placement_time(bot, order_id) for order_id in
                                                              [bot.take1, bot.take2]):
                    if bot.take1 != 'Filled':
                        bot.take1, bot.take2 = '', ''
                        bot.save()
                    else:
                        bot.take2 = ''
                        bot.save()
                    first_cycle = False
            else:
                if not order_placement_verification(bot, bot.take2) or not check_order_placement_time(bot, bot.take2):
                    bot.take2 = ''
                    bot.save()
                    first_cycle = False

            if first_cycle:
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

            if take2_status_check(bot):
                actions_after_end_cycle(bot)
                lock.acquire()
                continue

            if bot.take1 != 'Filled' and take1_status_check(bot):
                first_cycle = False

            if not first_cycle or tl != bb_obj.tl or bl != bb_obj.bl:
                cancel_all(bot.account, bot.category, bot.symbol)

                tl = bb_obj.tl
                bl = bb_obj.bl
                side = "Buy" if psn_side == "Sell" else "Sell"

                qty = psn_qty
                if bot.take_on_ml:
                    qty_ml = Decimal(str(psn_qty * bot.take_on_ml_percent / 100)).quantize(Decimal(bot.symbol.minOrderQty))

                if side == "Buy":
                    ml = bb_obj.ml
                    exit_line = bl
                    bin_line = tl
                    bin_side = "Sell"
                    if ml > psn_price * Decimal(str(0.999)):
                        new_ml = round(psn_price * Decimal(str(0.999)), round_number)
                        if ml == new_ml:
                            ml -= Decimal(bot.symbol.tickSize)
                        else:
                            ml = new_ml
                    if exit_line > psn_price * Decimal(str(0.998)):
                        new_exit_line = round(psn_price * Decimal(str(0.998)), round_number)
                        if exit_line == new_exit_line:
                            exit_line -= Decimal(bot.symbol.tickSize) * 2
                        else:
                            exit_line = new_exit_line
                else:
                    ml = bb_obj.ml
                    exit_line = tl
                    bin_line = bl
                    bin_side = "Buy"
                    if ml < psn_price * Decimal(str(1.001)):
                        new_ml = round(psn_price * Decimal(str(1.001)), round_number)
                        if ml == new_ml:
                            ml += Decimal(bot.symbol.tickSize)
                        else:
                            ml = new_ml
                    if exit_line < psn_price * Decimal(str(1.002)):
                        new_exit_line = round(psn_price * Decimal(str(1.002)), round_number)
                        if exit_line == new_exit_line:
                            exit_line += Decimal(bot.symbol.tickSize) * 2
                        else:
                            exit_line = new_exit_line

                if bot.bin_order:
                    if bot.bin_order_id:
                        if bin_order_buy_in_addition(bot, bin_side):
                            bot.bin_order_id = ''
                            bot.take1 = ''
                            bot.save()
                            lock.acquire()
                            continue

                if bot.take_on_ml:
                    if take1_status_check(bot):
                        take2 = Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side=side,
                            orderType='Limit',
                            qty=qty,
                            price=exit_line,
                            is_take=True,
                        )

                        if bot.bin_order:
                            bin_qty = Decimal(str((qty / (100 - bot.take_on_ml_percent)) * bot.take_on_ml_percent)).quantize(Decimal(bot.symbol.minOrderQty))

                            bin_order = Order.objects.create(
                                bot=bot,
                                category=bot.category,
                                symbol=bot.symbol.name,
                                side=bin_side,
                                orderType='Limit',
                                qty=bin_qty,
                                price=bin_line,
                            )
                            bot.bin_order_id = bin_order.orderLinkId
                            logging(bot, f'open BIN-order. Price: {exit_line}')

                        logging(bot, f'open take2 order. Price: {exit_line}')
                        bot.take2 = take2.orderLinkId
                        bot.save()

                    else:
                        if order_leaves_qty_check(bot, bot.take1):
                            qty_ml = bot.take2_amount
                        take1 = Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side=side,
                            orderType='Limit',
                            qty=qty_ml,
                            price=ml,
                            is_take=True,
                        )

                        take2 = Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side=side,
                            orderType='Limit',
                            qty=qty - qty_ml,
                            price=exit_line,
                            is_take=True,
                        )

                        logging(bot, f'open take1, take2 order. Price: {ml}, {exit_line}')
                        bot.take1, bot.take2 = take1.orderLinkId, take2.orderLinkId
                        bot.save()
                else:
                    take2 = Order.objects.create(
                        bot=bot,
                        category=bot.category,
                        symbol=bot.symbol.name,
                        side=side,
                        orderType='Limit',
                        qty=qty,
                        price=exit_line,
                        is_take=True,
                    )

            new_cycle = False
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


