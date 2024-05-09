import time
import traceback

from django.core.cache import cache

from api_2.api_aggregator import cancel_all_orders
from api_2.custom_ws_class import CustomWSClient
from .handlers_messages import zinger_handler_wrapper_market
from .worker_class import WorkZingerClassMarket

from ...general_functions import custom_logging, clear_cache_bot_data


def zinger_worker_market(bot):
    ws_client = None
    try:
        worker_class = WorkZingerClassMarket(bot)

        ''' Connection WS '''
        ws_client = CustomWSClient(callback=zinger_handler_wrapper_market(worker_class), bot=bot)
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
        cancel_all_orders(bot)
        try:
            if ws_client is not None:
                ws_client.exit()

            clear_cache_bot_data(bot.id)
            print('End working ZINGER bot')
        except Exception as e:
            print('ERROR:', e)
            custom_logging(bot, f'Error {e}')

        if bot.is_active:
            bot.is_active = False
            bot.save()



