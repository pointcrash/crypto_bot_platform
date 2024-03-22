import logging
import time
import traceback

from api_2.custom_ws_class import CustomWSClient
from .bb_worker_class import WorkBollingerBandsClass

from .handlers_messages import bb_handler_wrapper
from ...bot_logic import custom_logging


def bb_worker(bot):
    ws_client = None
    try:
        bb_worker_class = WorkBollingerBandsClass(bot)

        ''' Connection WS '''
        ws_client = CustomWSClient(callback=bb_handler_wrapper(bb_worker_class), bot=bot)
        ws_client.start()

        time.sleep(5)

        ''' Change leverage and position mode '''
        bb_worker_class.preparatory_actions()

        ''' Subscribe to topics '''
        ws_client.sub_to_user_info()
        ws_client.sub_to_kline()
        ws_client.sub_to_mark_price()

        while bot.is_active and ws_client.is_connected():
            time.sleep(5)
            bot.refresh_from_db()

    except Exception as e:
        logging.error(f"**Ошибка:** {e}")
        logging.error(f"**Аргументы ошибки:** {e.args}")
        logging.error(f"**Traceback:**")
        traceback.print_exc()
        custom_logging(bot, f'Error {e}')

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


