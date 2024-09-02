import time
import traceback
from datetime import datetime

from api_2.custom_ws_class import CustomWSClient
from .bot_worker_class import WorkGridClass

from .handlers_messages import grid_handler_wrapper
from ...general_functions import custom_logging, clear_cache_bot_data


def grid_worker(bot):
    bot.cycle_time_start = datetime.now()
    bot.save()

    ws_client = None
    try:
        worker_class = WorkGridClass(bot)

        ''' Connection WS '''
        ws_client = CustomWSClient(callback=grid_handler_wrapper(worker_class), bot=bot)
        ws_client.start()

        time.sleep(5)

        ''' Subscribe to klines, position and order info topics '''
        ws_client.sub_to_user_info()
        # ws_client.sub_to_kline(interval=bot.bb.interval)

        ''' Subscribe to mark price topic '''
        ws_client.sub_to_mark_price()

        ''' Change leverage and position mode '''
        worker_class.preparatory_actions()

        worker_class.initial_placing_orders()

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

            clear_cache_bot_data(bot.id)
            print('End working bb bot')
        except Exception as e:
            print('ERROR:', e)
            custom_logging(bot, f'Ошибка: {e}')
            custom_logging(bot, f'Traceback {traceback.format_exc()}')
        if bot.is_active:
            bot.is_active = False
            bot.save()




