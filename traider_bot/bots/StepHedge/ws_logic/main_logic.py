from pybit.unified_trading import WebSocket
import time

from bots.StepHedge.ws_logic.handlers_messages import handle_stream_callback
from bots.StepHedge.ws_logic.ws_step_class import WSStepHedgeClassLogic
from bots.bot_logic import lock_release, logging, exit_by_exception
from single_bot.logic.global_variables import lock, global_list_bot_id


def ws_step_hedge_bot_main_logic(bot, step_hg):
    bot_id = bot.pk
    step_class_obj = WSStepHedgeClassLogic(bot, step_hg)

    ws_private = WebSocket(
        testnet=not bot.account.is_mainnet,
        channel_type="private",
        api_key=bot.account.API_TOKEN,
        api_secret=bot.account.SECRET_KEY,
    )
    # ws_public = WebSocket(
    #     testnet=not bot.account.is_mainnet,
    #     channel_type="linear",
    # )

    ws_private.position_stream(callback=handle_stream_callback(step_class_obj, arg='position'))
    ws_private.order_stream(callback=handle_stream_callback(step_class_obj, arg='order'))

    # Выполняем подготовительные действия для старта работы бота
    step_class_obj.preparatory_actions()

    # Проверяем имеются ли открытые позиции
    if not step_class_obj.checking_opened_positions():
        # Проверяем указана ли точка входа и закупаемся
        if bot.price:
            step_class_obj.buy_by_limit()
        else:
            step_class_obj.buy_by_market()
    else:
        raise Exception('Имеются открытые позиции по данной торговой паре')

    # ws_public.ticker_stream(symbol=bot.symbol.name, callback=handle_stream_callback(step_class_obj, arg='ticker'))
    t = True
    # Запускаем цикл отслеживания состояния позиций
    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            lock_release()
            if t is True:
                t = False

                # Обновляем книгу ордеров до отмены ордеров
                status_req_order_book = step_class_obj.update_order_book()
                if status_req_order_book not in 'OK':
                    logging(bot, f'ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ -- {step_class_obj.order_book}')
                    raise Exception('ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ')
                # Обновляем список позиций
                step_class_obj.update_symbol_list()
                if step_class_obj.symbol_list is None:
                    logging(bot, f'ОШИБКА ПОЛУЧЕНИЯ "SYMBOL LIST"')
                    raise Exception('ОШИБКА ПОЛУЧЕНИЯ "SYMBOL LIST"')

                for position_number in range(2):
                    if step_class_obj.losses_pnl_check(position_number):
                        step_class_obj.average_psn(position_number)

                    if step_hg.add_tp:
                        if not step_class_obj.tp_full_size_psn_check(position_number):
                            if step_class_obj.psn_size_bigger_then_start(position_number):
                                step_class_obj.add_tp(position_number)
                            else:
                                if step_class_obj.checking_opened_position(position_number):
                                    step_class_obj.place_tp_order(position_number)
                    else:
                        if step_class_obj.checking_opened_position(position_number):
                            step_class_obj.place_tp_order(position_number)

                    if not step_hg.is_nipple_active:
                        if not step_class_obj.checking_opened_new_psn_order(position_number):
                            step_class_obj.place_nipple_on_tp(position_number)
                    else:
                        if not step_class_obj.checking_opened_new_psn_order(position_number):
                            step_class_obj.place_new_psn_order(position_number)
                        else:
                            if not step_class_obj.checking_opened_position(position_number):
                                if step_class_obj.distance_between_price_and_order_check(position_number):
                                    step_class_obj.amend_new_psn_order(position_number)

                    # выставление усредняющего ордера
                    step_class_obj.limit_average_psn(position_number)

            if not ws_private.is_connected():
                raise ConnectionError('Private WebSocket connected error')
            # if not ws_public.is_connected():
            #     raise ConnectionError('Public WebSocket connected error')
            time.sleep(2)
            lock.acquire()
    except Exception as e:
        logging(bot, f'Error {e}')
        lock.acquire()
        try:
            exit_by_exception(bot)
        finally:
            lock_release()
    finally:
        lock_release()


def handle_execution_stream_message(message):
    print('--------------------START--EXECUTION-LIST----------------------')
    for i in message['data']:
        print(i)
    print('--------------------END--EXECUTION-LIST------------------------')
    print()


'''
    {'category': 'linear', 'symbol': 'SANDUSDT', 'orderId': 'be4282e3-ca8b-42da-81b2-4baa924eeec0', 'orderLinkId': '2cb6fe4967594e869816b7605abf05f6', 'blockTradeId': '', 'side': 'Buy', 'positionIdx': 1, 'o
    rderStatus': 'Filled', 'cancelType': 'UNKNOWN', 'rejectReason': 'EC_NoError', 'timeInForce': 'IOC', 'isLeverage': '', 'price': '0.3936', 'qty': '2665', 'avgPrice': '0.375', 'leavesQty': '0', 'leavesValu
    e': '0', 'cumExecQty': '2665', 'cumExecValue': '999.375', 'cumExecFee': '0.39975', 'orderType': 'Market', 'stopOrderType': '', 'orderIv': '', 'triggerPrice': '', 'takeProfit': '', 'stopLoss': '', 'trigg
    erBy': '', 'tpTriggerBy': '', 'slTriggerBy': '', 'triggerDirection': 0, 'placeType': '', 'lastPriceOnCreated': '0.3749', 'closeOnTrigger': False, 'reduceOnly': False, 'smpGroup': 0, 'smpType': 'None', 'smpOrderId': '', 'slLimitPrice': '0', 'tpLimitPrice': '0', 'tpslMode': 'UNKNOWN', 'createdTime': '1699202320338', 'updatedTime': '1699202320342', 'feeCurrency': ''}
    {'retCode': 0, 'retMsg': 'OK', 'result': {}, 'retExtInfo': {}, 'time': 1699202320603}
'''
