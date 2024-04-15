import time
import traceback

from api_2.custom_ws_class import CustomWSClient
from .handlers_messages import zinger_handler_wrapper
from .worker_class import WorkZingerClass

from ...general_functions import custom_logging


def zinger_worker(bot):
    ws_client = None
    try:
        worker_class = WorkZingerClass(bot)

        ''' Connection WS '''
        ws_client = CustomWSClient(callback=zinger_handler_wrapper(worker_class), bot=bot)
        ws_client.start()

        time.sleep(5)

        ''' Subscribe to topics '''
        ws_client.sub_to_user_info()
        ws_client.sub_to_mark_price()

        ''' Change leverage and position mode '''
        worker_class.preparatory_actions()

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
            print('End working ZINGER bot')
        except Exception as e:
            print('ERROR:', e)
            custom_logging(bot, f'Error {e}')
        if bot.is_active:
            bot.is_active = False
            bot.save()



