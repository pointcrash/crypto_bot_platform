import os
import signal

import psutil
from django.db import connections

from api_v5 import cancel_all, get_list, get_side, get_qty
from bots.bot_logic import logging
from bots.models import Take, AvgOrder, SingleBot
from orders.models import Order
from single_bot.logic.global_variables import lock, global_list_threads


def terminate_process_by_pid(bot_id):
    lock.acquire()
    try:
        if bot_id in global_list_threads:
            global_list_threads.remove(bot_id)
            return f"Terminate successful"
    except:
        return "terminate error"
    finally:
        lock.release()


def check_thread_alive(bot_id):
    lock.acquire()
    try:
        if bot_id in global_list_threads:
            return True
        else:
            return False
    finally:
        lock.release()


def drop_position(bot):
    symbol_list = get_list(bot.account, bot.category, bot.symbol)
    psn_qty = get_qty(symbol_list)
    psn_side = get_side(symbol_list)

    if type([]) == type(psn_qty):
        for qty, side in zip(psn_qty, psn_side):
            if qty:
                order_side = "Buy" if side == "Sell" else "Sell"

                drop_order = Order.objects.create(
                    bot=bot,
                    category=bot.category,
                    symbol=bot.symbol.name,
                    side=order_side,
                    orderType='Market',
                    qty=qty,
                    is_take=True,
                )
    else:
        order_side = "Buy" if psn_side == "Sell" else "Sell"

        drop_order = Order.objects.create(
            bot=bot,
            category=bot.category,
            symbol=bot.symbol.name,
            side=order_side,
            orderType='Market',
            qty=psn_qty,
            is_take=True,
        )


def stop_bot_with_cancel_orders(bot):
    avg_order = AvgOrder.objects.filter(bot=bot).first()
    takes = Take.objects.filter(bot=bot)
    if takes:
        takes.delete()
    if avg_order:
        avg_order.delete()
    connections.close_all()

    logging(bot, terminate_process_by_pid(bot.pk))
    logging(bot, 'cancel all orders' if cancel_all(bot.account, bot.category, bot.symbol)[
                                            'retMsg'] == 'OK' else 'error when canceling orders')


def stop_bot_with_cancel_orders_and_drop_positions(bot):
    drop_position(bot)
    stop_bot_with_cancel_orders(bot)
    logging(bot, 'drop position')
