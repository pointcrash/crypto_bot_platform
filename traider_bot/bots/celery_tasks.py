import logging

from celery import shared_task

from bots.bb.logic.start_logic import bb_bot_ws_connect
from bots.grid.logic.start_logic import grid_bot_ws_connect
from bots.models import BotModel

logger = logging.getLogger('debug_logger')


@shared_task
def run_bot_ws_socket(bot_id):
    bot = BotModel.objects.get(pk=bot_id)

    if bot.work_model == 'bb':
        bb_bot_ws_connect(bot)

    elif bot.work_model == 'grid':
        grid_bot_ws_connect(bot)
