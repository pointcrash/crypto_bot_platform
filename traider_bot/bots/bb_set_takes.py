import time

from decimal import Decimal

from api_v5 import cancel_all, switch_position_mode, set_leverage
from bots.bot_logic import calculation_entry_point, take1_status_check, logging, \
    take2_status_check, create_bb_and_avg_obj, bot_stats_clear, take1_leaves_qty_check, order_placement_verification, \
    check_order_placement_time
from orders.models import Order
from single_bot.logic.global_variables import lock, global_list_bot_id, global_list_threads
from single_bot.logic.work import append_thread_or_check_duplicate
from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message


def set_takes(bot):
    new_cycle = True
    bot_id = bot.pk
    is_ts_bot = True if bot.side == 'TS' else False
    append_thread_or_check_duplicate(bot_id, is_ts_bot)

    if not is_ts_bot:
        tg = TelegramAccount.objects.filter(owner=bot.owner).first()
        if tg:
            chat_id = tg.chat_id
            send_telegram_message(chat_id, f'Bot {bot.pk} - {bot} started work')
        switch_position_mode(bot)
        set_leverage(bot.account, bot.category, bot.symbol, bot.isLeverage)

    bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()

            if take2_status_check(bot):
                actions_after_end_cycle(bot)
                continue

            '''  Функция установки точек входа и усреднения  '''
            try:
                psn_qty, psn_side, psn_price, first_cycle = calculation_entry_point(bot=bot, bb_obj=bb_obj, bb_avg_obj=bb_avg_obj)
            except Exception as e:
                if isinstance(e, TypeError):
                    lock.acquire()
                    continue
                else:
                    raise ValueError(f'Ошибка в блоке calculation_entry_point: {e}')

            tl = bb_obj.tl
            bl = bb_obj.bl

            if not new_cycle:
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

            if first_cycle:  # Not first cycle (-_-)
                time.sleep(bot.time_sleep)

            if not first_cycle or tl != bb_obj.tl or bl != bb_obj.bl:
                cancel_all(bot.account, bot.category, bot.symbol)

                tl = bb_obj.tl
                bl = bb_obj.bl
                side = "Buy" if psn_side == "Sell" else "Sell"

                qty = psn_qty
                if bot.take_on_ml:
                    qty_ml = (Decimal(psn_qty * bot.take_on_ml_percent / 100)).quantize(Decimal(bot.symbol.minOrderQty))

                if side == "Buy":
                    ml = bb_obj.ml
                    exit_line = bl
                else:
                    ml = bb_obj.ml
                    exit_line = tl

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

                        logging(bot, f'open take2 order. Price: {exit_line}')
                        bot.take2 = take2.orderLinkId
                        bot.save()

                    else:
                        if take1_leaves_qty_check(bot):
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


def actions_after_end_cycle(bot):
    bot_id = bot.pk
    logging(bot, f'bot finished work. P&L: {bot.pnl}')
    if not bot.repeat:
        lock.acquire()
        try:
            global_list_bot_id.remove(bot_id)
            if bot_id not in global_list_bot_id:
                del global_list_threads[bot_id]
        finally:
            if lock.locked():
                lock.release()
    else:
        bot_stats_clear(bot)
