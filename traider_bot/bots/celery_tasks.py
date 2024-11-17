import logging
import os
import time

from celery import shared_task
from django.core.cache import cache

from bots.bb.logic.start_logic import bb_bot_ws_connect
from bots.grid.logic.start_logic import grid_bot_ws_connect
from bots.models import BotModel

logger = logging.getLogger('debug_logger')


@shared_task(queue=os.getenv('CELERY_QUEUE_NAME'))
def run_bot_ws_socket(bot_id):
    bot = BotModel.objects.get(pk=bot_id)

    if bot.work_model == 'bb':
        bb_bot_ws_connect(bot)

    elif bot.work_model == 'grid':
        grid_bot_ws_connect(bot)


@shared_task(queue=os.getenv('CELERY_QUEUE_NAME'))
def recreate_bots_with_new_celery_worker():
    pattern = 'ws-*-q-*'
    keys = cache.keys(pattern)

    for key in keys:
        bot_id = next(x for x in key.split('-') if x.isdigit())
        cache.set(f'close_ws_{bot_id}', True, timeout=60)

        while cache.get(f'close_ws_{bot_id}'):
            time.sleep(0.3)

        logger.debug(f'bot_{bot_id}socket must be restart run_bot_ws_socket.delay')
        run_bot_ws_socket.delay(bot_id)  # Отдаем задачу запуска сокета - Селери
