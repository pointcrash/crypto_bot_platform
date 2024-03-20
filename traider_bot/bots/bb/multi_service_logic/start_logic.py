import time
import traceback

from api.custom_ws_class import CustomWebSocketClient
from .bb_worker_class import WorkBollingerBandsClass

from .handlers_messages import bb_handler_wrapper
from ...bot_logic import logging


def bb_worker(bot):
    ws_client = None
    try:
        bb_worker_class = WorkBollingerBandsClass(bot)

        ''' Connection WS '''
        ws_client = CustomWebSocketClient(callback=bb_handler_wrapper(bb_worker_class),
                                          account_name=bot.account.name,
                                          service_name=bot.account.service.name
                                          )
        ws_client.start()

        time.sleep(5)

        ''' Change leverage and position mode '''
        bb_worker_class.preparatory_actions()

        ''' Subscribe to topics '''
        ws_client.sub_to_kline(symbol=bot.symbol.name, interval=bot.interval)
        ws_client.sub_to_mark_price(symbol=bot.symbol.name)

        while bot.is_active and ws_client.websocket.open:
            time.sleep(3)

    except Exception as e:
        print(f"**Ошибка:** {e}")
        print(f"**Аргументы ошибки:** {e.args}")
        print(f"**Traceback:**")
        traceback.print_exc()
        logging(bot, f'Error {e}')

    finally:
        try:
            ws_client.close()
            print('End working bb bot')
        except Exception as e:
            print('ERROR:', e)
            logging(bot, f'Error {e}')
        if bot.is_active:
            bot.is_active = False
            bot.save()


