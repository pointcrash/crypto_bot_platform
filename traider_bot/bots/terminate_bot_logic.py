import os
import signal

import psutil

from api_v5 import cancel_all, get_list, get_side, get_qty
from main.models import Log
from orders.models import Order


def terminate_process_by_pid(pid):
    if pid is not None:
        pid = int(pid)
        if get_status_process(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Process with PID {pid} terminated successfully.")
            except OSError as e:
                print(f"Error terminating process with PID {pid}: {e}")


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
    psn_qty, psn_side = get_qty(symbol_list), get_side(symbol_list)
    side = "Buy" if psn_side == "Sell" else "Sell"

    drop_order = Order.objects.create(
        bot=bot,
        category=bot.category,
        symbol=bot.symbol,
        side=side,
        orderType='Market',
        qty=psn_qty,
        is_take=True,
    )


def stop_bot_with_cancel_orders(bot):
    terminate_process_by_pid(bot.process_id)
    cancel_all(bot.account, bot.category, bot.symbol)
    Log.objects.create(content="Bot stopped and cancel all orders is success")


def stop_bot_with_cancel_orders_and_drop_positions(bot):
    terminate_process_by_pid(bot.process_id)
    cancel_all(bot.account, bot.category, bot.symbol)
    drop_position(bot)
    Log.objects.create(content="Bot stopped, cancel all orders and drop position is success")