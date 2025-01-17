import time
import traceback
from datetime import datetime

from api_2.custom_ws_class import CustomWSClient
from .bot_worker_class import WorkBollingerBandsClass

from .handlers_messages import bb_handler_wrapper
from ...general_functions import custom_logging, clear_cache_bot_data, custom_user_bot_logging


def bb_bot_ws_connect(bot):
    bb_worker_class = WorkBollingerBandsClass(bot)
    custom_user_bot_logging(bot, 'Бот запущен')

    ''' Connection WS '''
    ws_client = CustomWSClient(callback=bb_handler_wrapper(bb_worker_class), bot=bot)
    ws_client.start()

    time.sleep(5)

    ''' Subscribe to klines, position and order info topics '''
    ws_client.sub_to_user_info()
    ws_client.sub_to_kline(interval=bot.bb.interval)

    ''' Change leverage and position mode '''
    bb_worker_class.preparatory_actions()

    ''' Subscribe to mark price topic '''
    ws_client.sub_to_mark_price()

    return ws_client


def bb_worker(bot):
    bot.cycle_time_start = datetime.now()
    bot.save()

    ws_client = None
    try:
        ws_client = bb_bot_ws_connect(bot)

        while bot.is_active and ws_client.is_connected():
            bot_time_update = bot.time_update
            bb_time_update = bot.bb.time_update

            time.sleep(5)

            bot.refresh_from_db()

            if bot.is_active:
                if bot.time_update != bot_time_update or bot.bb.time_update != bb_time_update:
                    ws_client.exit()
                    ws_client = bb_bot_ws_connect(bot)

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
