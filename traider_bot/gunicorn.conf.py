import os
import django

import multiprocessing
from bots.bb_set_takes import set_takes
from bots.bot_logic_grid import set_takes_for_grid_bot
from bots.hedge.grid_logic import set_takes_for_hedge_grid_bot
from bots.bot_logic import create_bb_and_avg_obj
from bots.terminate_bot_logic import get_status_process, terminate_process_by_pid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from bots.models import Bot


def on_starting(server):
    bots = Bot.objects.all()
    for bot in bots:
        bot_process = None
        if bot.process.pid:
            bb_obj, bb_avg_obj = create_bb_and_avg_obj(bot)
            if bot.category == 'linear':
                if bot.work_model == 'grid':
                    bot_process = multiprocessing.Process(target=set_takes_for_grid_bot, args=(bot, bb_obj, bb_avg_obj))
                elif bot.work_model == 'bb':
                    bot_process = multiprocessing.Process(target=set_takes, args=(bot, bb_obj, bb_avg_obj))
            elif bot.category == 'inverse':
                if bot.work_model == 'grid':
                    bot_process = multiprocessing.Process(target=set_takes_for_hedge_grid_bot, args=(bot,))
                elif bot.work_model == 'bb':
                    pass
        if bot_process:
            bot_process.start()
            bot.process.pid = str(bot_process.pid)
            bot.process.save()


def on_exit(server):
    bots = Bot.objects.all()
    for bot in bots:
        if get_status_process(bot.process.pid):
            terminate_process_by_pid(bot.process.pid)


def when_ready(server):
    on_starting(server)


def worker_exit(server, worker):
    on_exit(server)
