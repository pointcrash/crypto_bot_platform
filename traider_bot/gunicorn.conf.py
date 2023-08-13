import os
import time
import pickle

import django

from bots.bb_set_takes import set_takes
from bots.bot_logic import create_bb_and_avg_obj, clear_data_bot
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from bots.terminate_bot_logic import terminate_thread, check_thread_alive, stop_bot_with_cancel_orders
from single_bot.logic.global_variables import *
from single_bot.logic.work import bot_work_logic

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from bots.models import Bot, IsTSStart


def bot_start_reboot(bot_id):
    bot = Bot.objects.get(pk=bot_id)
    bot_thread = None
    is_ts_start = IsTSStart.objects.filter(bot=bot)

    if check_thread_alive(bot.pk):
        stop_bot_with_cancel_orders(bot)

    clear_data_bot(bot)  # Очищаем данные ордеров и тейков которые использовал старый бот

    if bot.work_model == 'bb':
        if bot.side == 'TS':
            if is_ts_start:
                bot_thread = threading.Thread(target=set_takes, args=(bot,))
            else:
                bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
        else:
            bot_thread = threading.Thread(target=set_takes, args=(bot,))
    elif bot.work_model == 'grid':
        if bot.side == 'TS':
            if is_ts_start:
                bot_thread = threading.Thread(target=bot_work_logic, args=(bot,))
            else:
                bot_thread = threading.Thread(target=set_takes_for_hedge_grid_bot, args=(bot,))
        else:
            bot_thread = threading.Thread(target=bot_work_logic, args=(bot,))

    if bot_thread is not None:
        bot_thread.start()
        lock.acquire()
        global_list_threads[bot.pk] = bot_thread
        if lock.locked():
            lock.release()


def worker_exit(server, worker):
    all_bots_pks = Bot.objects.values_list('pk', flat=True).order_by('pk')
    for bot_id in all_bots_pks:
        print(terminate_thread(bot_id))


def when_ready(server):
    try:
        all_bots_pks = Bot.objects.values_list('pk', flat=True).order_by('pk')
        for bot_id in all_bots_pks:
            print(terminate_thread(bot_id))

        time.sleep(5)

        for bot_id in all_bots_pks:
            bot_start_reboot(bot_id=bot_id)

        print('Запуск произведен')

    except Exception as e:
        print(f'При старте воркера возникла ошибка {e}')