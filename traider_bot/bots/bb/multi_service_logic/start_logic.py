import time

from api.custom_ws_class import CustomWebSocketClient
from main.models import ActiveBot
from .bb_worker_class import WorkBollingerBandsClass

from .handlers_messages import bb_handler_wrapper
from ...bot_logic import is_bot_active, logging


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

        time.sleep(3)
        # print('Conn status', ws_client.is_open())

        ''' Change leverage and position mode '''
        bb_worker_class.preparatory_actions()

        ''' Subscribe to topics '''
        ws_client.sub_to_kline(symbol=bot.symbol.name, interval=bot.interval)
        ws_client.sub_to_mark_price(symbol=bot.symbol.name)

        while is_bot_active(bot.id):
            # print('TL = ', bb_worker_class.bb.tl, 'BL = ', bb_worker_class.bb.bl)
            # print(bb_worker_class.position_info, bb_worker_class.have_psn)
            # print('.')
            time.sleep(3)

    except Exception as e:
        print(e)
        logging(bot, f'Error {e}')
        # exit_by_exception(bot)

    finally:
        try:
            ws_client.close()
            print('End working bb bot')
        except Exception as e:
            print('ERROR:', e)
            logging(bot, f'Error {e}')
        if is_bot_active(bot.id):
            ActiveBot.objects.filter(bot_id=bot.id).delete()


