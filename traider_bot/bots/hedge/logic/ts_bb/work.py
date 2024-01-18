from api.api_v5 import get_qty, get_side, get_position_price
from bots.bb_set_takes import set_takes
from bots.bot_logic import create_bb_and_avg_obj, func_get_symbol_list
from orders.models import Order
from single_bot.logic.global_variables import lock, global_list_bot_id
from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message


def work_ts_bb_bot(bot):
    bot_id = bot.pk
    bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)
    # append_thread_or_check_duplicate(bot_id, is_ts_bot=False)

    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            if lock.locked():
                lock.release()

            symbol_list = func_get_symbol_list(bot)
            for position_idx in [0, 1]:
                psn_qty = get_qty(symbol_list)[position_idx]
                psn_side = get_side(symbol_list)[position_idx]
                psn_price = get_position_price(symbol_list)[position_idx]

                bb_avg_obj.psn_price = psn_price
                bb_avg_obj.psn_side = psn_side
                bb_avg_obj.psn_qty = psn_qty

                if bot.work_model == "bb" and bb_avg_obj is not None:
                    if bb_avg_obj.auto_avg():
                        position_idx = 1 if position_idx == 0 else 0
                        psn_side = get_side(symbol_list)[position_idx]
                        side = "Buy" if psn_side == "Sell" else "Sell"
                        take = Order.objects.create(
                            bot=bot,
                            category=bot.category,
                            symbol=bot.symbol.name,
                            side=side,
                            orderType='Market',
                            qty=psn_qty,
                            is_take=True,
                        )
                        ''' После усреднения одной и закрытия другой позиции
                         передаем управление одностороннему bb боту '''
                        set_takes(bot)
                        ''' После ее выполнения выходим из цикла '''
                        break
            lock.acquire()

    finally:
        tg = TelegramAccount.objects.filter(owner=bot.owner).first()
        if tg:
            chat_id = tg.chat_id
            send_telegram_message(chat_id, f'Bot {bot.pk} - {bot} finished work')
        if lock.locked():
            lock.release()
