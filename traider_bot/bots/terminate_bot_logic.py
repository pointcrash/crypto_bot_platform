import os
import signal

import psutil
from django.db import connections

from api_v5 import cancel_all, get_list, get_side, get_qty
from bots.bot_logic import logging
from bots.models import Take, AvgOrder, SingleBot
from orders.models import Order


def terminate_process_by_pid(bot):
    pid = bot.process.pid
    if pid is not None:
        pid = int(pid)
        if get_status_process(pid):
            try:
                SingleBot.objects.get(bot=bot).delete()
                os.kill(pid, signal.SIGTERM)
                # connections.close_all()
                return "Bot terminated successfully."
            except OSError as e:
                # connections.close_all()
                return f"Error terminating process with PID {pid}: {e}"


def get_status_process(pid):
    if pid is not None:
        try:
            process = psutil.Process(int(pid))
            if process.is_running():
                return True
            else:
                return False
        except:
            return False
    return False


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
    # connections.close_all()

    logging(bot, terminate_process_by_pid(bot))
    logging(bot, 'cancel all orders' if cancel_all(bot.account, bot.category, bot.symbol)[
                                            'retMsg'] == 'OK' else 'error when canceling orders')


def stop_bot_with_cancel_orders_and_drop_positions(bot):
    stop_bot_with_cancel_orders(bot)
    # logging(bot, terminate_process_by_pid(bot.process.pid))
    # logging(bot, 'cancel all orders' if cancel_all(bot.account, bot.category, bot.symbol)[
    #                                         'retMsg'] == 'OK' else 'error when canceling orders')
    drop_position(bot)
    logging(bot, 'drop position')
