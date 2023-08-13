import os
import threading

import django

from bots.bb_set_takes import set_takes
from bots.bot_logic import clear_data_bot
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from single_bot.logic.global_variables import *
from single_bot.logic.work import bot_work_logic

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from bots.models import Bot, IsTSStart


def bot_start_reboot(bot_id):
    import threading

    bot = Bot.objects.get(pk=bot_id)
    print(bot.is_active)
    if bot.is_active:
        bot_thread = None
        is_ts_start = IsTSStart.objects.filter(bot=bot)

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


def stop_bot(bot_id):
    import threading

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
                return f"Terminate successful"
    except Exception as e:
        return f"Terminate error: {e}"
    finally:
        if lock.locked():
            lock.release()


def worker_exit(server, worker):
    all_bots_pks = Bot.objects.values_list('pk', flat=True).order_by('pk')
    for bot_id in all_bots_pks:
        print(stop_bot(bot_id))


def when_ready(server):
    import time

    try:
        all_bots_pks = Bot.objects.values_list('pk', flat=True).order_by('pk')
        lock.acquire()
        print(global_list_bot_id)
        print(all_bots_pks)
        if lock.locked():
            lock.release()
        time.sleep(5)

        for bot_id in all_bots_pks:
            bot_start_reboot(bot_id=bot_id)
            print(f'Запуск произведен {bot_id}')

    except Exception as e:
        print(f'При старте воркера возникла ошибка {e}')