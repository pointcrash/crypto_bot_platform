import os
import time
import pickle

import django

from bots.bb_set_takes import set_takes
from bots.bot_logic import create_bb_and_avg_obj
from bots.hedge.logic.work import set_takes_for_hedge_grid_bot
from single_bot.logic.global_variables import *
from single_bot.logic.work import bot_work_logic

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from bots.models import Bot, IsTSStart


def when_ready(server):
    time.sleep(10)
    try:
        with open("bot_id.pkl", "rb") as file:
            bot_id_list = pickle.load(file)
        if bot_id_list:
            server.log.info(bot_id_list)
            for bot_id in bot_id_list:
                bot = Bot.objects.filter(pk=bot_id).first()
                if bot:
                    bot_thread = None
                    is_ts_start = IsTSStart.objects.filter(bot=bot)
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
                        global_list_threads[bot_id] = bot_thread
                        lock.release()
    except Exception as e:
        server.log.info(f"Error starting threads - {e}")

    finally:
        server.log.info("Gunicorn is ready to accept requests.")


def worker_exit(server, worker):
    try:
        os.remove("bot_id.pkl")
        print("Файл успешно удален.")
    except FileNotFoundError:
        print("Файл не найден.")
    except PermissionError:
        print("Отсутствуют права доступа для удаления файла.")
    except Exception as e:
        print(f"Ошибка при удалении файла: {e}")
    lock.acquire()
    try:
        if global_list_threads:
            with open("bot_id.pkl", "wb") as file:
                pickle.dump(list(global_list_threads.keys()), file)
            global_list_threads.clear()
    finally:
        lock.release()
        server.log.info(f"Worker {worker.pid} has exited.")
