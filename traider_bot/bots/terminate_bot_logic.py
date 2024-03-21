import time

from api.api_v5_bybit import cancel_all, get_list, get_side, get_qty
from bots.bot_logic import custom_logging, clear_data_bot
from bots.models import Bot
from main.models import ActiveBot
from orders.models import Order
from single_bot.logic.global_variables import lock, global_list_bot_id, global_list_threads


def terminate_thread(bot_id, keep_active=False):
    bot = Bot.objects.get(pk=bot_id)
    if ActiveBot.objects.filter(bot_id=bot_id):
        ActiveBot.objects.filter(bot_id=bot_id).delete()
        time.sleep(5)
    lock.acquire()
    try:
        if bot_id in global_list_bot_id:
            global_list_bot_id.remove(bot_id)
            if bot_id not in global_list_bot_id:
                thread = global_list_threads[bot_id]
                if lock.locked():
                    lock.release()
                thread.join()
                lock.acquire()
                del global_list_threads[bot_id]
                return f"Terminate successful {bot_id}"
    except Exception as e:
        return f"Terminate error: {e}"
    finally:
        bot.is_active = False
        bot.save()
        if not keep_active:
            pass
            # bot.is_active = False
            # bot.save()
        if lock.locked():
            lock.release()


def check_thread_alive(bot_id):
    lock.acquire()
    try:
        if bot_id in global_list_bot_id:
            return True
        else:
            return False
    finally:
        if lock.locked():
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
    custom_logging(bot, terminate_thread(bot.pk))
    custom_logging(bot, 'cancel all orders' if cancel_all(bot.account, bot.category, bot.symbol)[
                                            'retMsg'] == 'OK' else 'error when canceling orders')


def stop_bot_with_cancel_orders_and_drop_positions(bot):
    drop_position(bot)
    stop_bot_with_cancel_orders(bot)
    custom_logging(bot, 'drop position')
