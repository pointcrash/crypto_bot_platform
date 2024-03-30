import logging
import time
import traceback

from api_2.custom_ws_class import CustomWSClient
from .bot_worker_class import WorkBollingerBandsClass

from .handlers_messages import bb_handler_wrapper
from ...general_functions import custom_logging

formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s')


def bb_worker(bot):
    ws_client = None
    logger = bot_get_logger(bot.id)
    try:
        bb_worker_class = WorkBollingerBandsClass(bot, logger)

        ''' Connection WS '''
        ws_client = CustomWSClient(callback=bb_handler_wrapper(bb_worker_class), bot=bot)
        ws_client.start()

        time.sleep(5)

        ''' Subscribe to topics '''
        ws_client.sub_to_user_info()
        ws_client.sub_to_kline(interval=bot.bb.interval)
        ws_client.sub_to_mark_price()

        ''' Change leverage and position mode '''
        bb_worker_class.preparatory_actions()

        while bot.is_active and ws_client.is_connected():
            time.sleep(5)
            bot.refresh_from_db()

    except Exception as e:
        bot.is_active = False
        bot.save()
        traceback.print_exc()
        custom_logging(bot, f"**Ошибка:** {e}")
        custom_logging(bot, f"**Traceback:** {traceback.format_exc()}")

    finally:
        try:
            if ws_client is not None:
                ws_client.exit()
            print('End working bb bot')
        except Exception as e:
            print('ERROR:', e)
            custom_logging(bot, f'Error {e}')
        if bot.is_active:
            bot.is_active = False
            bot.save()


def bot_get_logger(bot_id):
    logger = logging.getLogger(f'BOT_{bot_id}')
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(f'logs/bot_{bot_id}.log')
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger

