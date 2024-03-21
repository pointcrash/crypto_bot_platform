import time

from api.custom_ws_class import CustomWebSocketClient
from main.models import ActiveBot
from .bot_class import WorkZingerVipClass
from .handlers import zinger_vip_handler_wrapper

from ...bot_logic import is_bot_active, custom_logging


def zinger_vip_worker(bot):
    ws_client = None
    try:
        worker_class = WorkZingerVipClass(bot)

        ''' Connection WS '''
        ws_client = CustomWebSocketClient(callback=zinger_vip_handler_wrapper(worker_class),
                                          account_name=bot.account.name,
                                          service_name=bot.account.service.name
                                          )
        ws_client.start()

        time.sleep(3)
        # print('Conn status', ws_client.is_open())

        ''' Change leverage and position mode '''
        worker_class.preparatory_actions()

        ''' Subscribe to topics '''
        # ws_client.sub_to_kline(symbol=bot.symbol.name, interval=bot.interval)
        ws_client.sub_to_mark_price(symbol=bot.symbol.name)

        ''' First open positions '''
        if not worker_class.check_opened_psn():
            worker_class.open_psns_with_start()

        ''' Empty cycle '''
        print(bot.is_active)
        while bot.is_active:
            # print('TL = ', bb_worker_class.bb.tl, 'BL = ', bb_worker_class.bb.bl)
            # print(bb_worker_class.position_info, bb_worker_class.have_psn)
            # print('.')
            time.sleep(3)

    except Exception as e:
        print(e)
        custom_logging(bot, f'Error {e}')
        # exit_by_exception(bot)

    finally:
        try:
            ws_client.close()
            print('End working bb bot')
        except Exception as e:
            print('ERROR:', e)
            custom_logging(bot, f'Error {e}')
        if bot.is_active:
            bot.is_active = False
            bot.save()
        # if is_bot_active(bot.id):
        #     ActiveBot.objects.filter(bot_id=bot.id).delete()


