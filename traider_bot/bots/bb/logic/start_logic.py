import time
import traceback

from api_2.custom_ws_class import CustomWSClient
from .bot_worker_class import WorkBollingerBandsClass

from .handlers_messages import bb_handler_wrapper
from ...general_functions import custom_logging, clear_cache_bot_data


def bb_worker(bot):
    ws_client = None
    try:
        bb_worker_class = WorkBollingerBandsClass(bot)

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

            bb = bot.bb
            bb.take_on_ml_status = bb_worker_class.ml_filled
            bb.take_on_ml_qty = bb_worker_class.ml_qty
            bb.save()

            clear_cache_bot_data(bot.id)
            print('End working bb bot')
        except Exception as e:
            print('ERROR:', e)
            custom_logging(bot, f'Ошибка: {e}')
            custom_logging(bot, f'Traceback {traceback.format_exc()}')
        if bot.is_active:
            bot.is_active = False
            bot.save()




