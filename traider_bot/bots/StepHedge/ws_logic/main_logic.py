import threading
from decimal import Decimal

from pybit.unified_trading import WebSocket
import time

from api_test.api_v5_bybit import cancel_all
from bots.StepHedge.ws_logic.handlers_messages import handle_stream_callback
from bots.StepHedge.ws_logic.ws_step_class import WSStepHedgeClassLogic
from bots.general_functions import custom_logging, exit_by_exception, is_bot_active
from bots.models import JsonObjectClass, StepHedge
from main.models import ActiveBot


def ws_step_hedge_bot_main_logic(bot, step_hg):
    ws_private = None
    ws_public = None
    bot_id = bot.pk

    try:
        class_data, created = JsonObjectClass.objects.get_or_create(
            bot=bot,
            bot_mode=bot.work_model,
            defaults={'data': dict()}
        )

        step_class_obj = WSStepHedgeClassLogic(bot, step_hg, class_data)
        # step_class_obj.class_data_obj.data['is_avg_psn_flag_dict'] = step_class_obj.is_avg_psn_flag_dict
        # step_class_obj.class_data_obj.save()

        ws_private = WebSocket(
            # trace_logging=True,
            testnet=not bot.account.is_mainnet,
            channel_type="private",
            api_key=bot.account.API_TOKEN,
            api_secret=bot.account.SECRET_KEY,
        )
        ws_public = WebSocket(
            testnet=not bot.account.is_mainnet,
            channel_type="linear",
        )

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
        # elif step_class_obj.checking_2opened_positions():
        else:
            cancel_all(step_class_obj.account, step_class_obj.category, step_class_obj.symbol)
        # else:
        #     raise Exception('Некорректное состояние позиций по данной торговой паре')

        ws_public.ticker_stream(symbol=bot.symbol.name, callback=handle_stream_callback(step_class_obj, arg='ticker'))

        # Обновляем книгу ордеров до отмены ордеров
        status_req_order_book = step_class_obj.update_order_book()
        if status_req_order_book not in 'OK':
            custom_logging(bot, f'ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ -- {step_class_obj.order_book}')
            raise Exception('ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ')
        # Обновляем список позиций
        step_class_obj.update_symbol_list()
        if step_class_obj.symbol_list is None:
            custom_logging(bot, f'ОШИБКА ПОЛУЧЕНИЯ "SYMBOL LIST"')
            raise Exception('ОШИБКА ПОЛУЧЕНИЯ "SYMBOL LIST"')

        for position_number in range(2):
            if step_class_obj.symbol_list[position_number]['size'] == '0':
                continue

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

        # Проверка наличия указанной маржи для позиций
        if step_class_obj.short1invest and step_class_obj.long1invest:
            position_idxs_list = [1, 2]
        else:
            if not step_class_obj.short1invest and not step_class_obj.long1invest:
                raise Exception('Не указана маржа открытия позиций')
            elif step_class_obj.short1invest:
                position_idxs_list = [2]
            else:
                position_idxs_list = [1]

        # Запускаем цикл отслеживания состояния позиций/ордеров
        while is_bot_active(bot_id):

            if not ws_public.is_connected():
                c = 0
                while not ws_public.is_connected():
                    if c > 100:
                        if not ws_private.is_connected():
                            custom_logging(bot, 'PRIVATE DISCONNECT TOO')
                        raise ConnectionError('Reconnection PUBLIC attempt limit exceeded')
                    time.sleep(1)
                    c += 1
                custom_logging(bot, 'DISCONNECT PUBLIC RECONNECTING')

            if not ws_private.is_connected():
                c = 0
                while not ws_private.is_connected():
                    if c > 100:
                        if not ws_public.is_connected():
                            custom_logging(bot, 'PUBLIC DISCONNECT TOO')
                        raise ConnectionError('Reconnection PRIVATE attempt limit exceeded')
                    time.sleep(1)
                    c += 1
                custom_logging(bot, 'DISCONNECT PRIVATE RECONNECTING')

            # Используем блокировку потока пока не выставиться следующий ордер
            step_class_obj.locker_3.acquire()

            # Обновляем книгу ордеров
            status_req_order_book = step_class_obj.update_order_book()
            if status_req_order_book not in 'OK':
                custom_logging(bot, f'ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ -- {step_class_obj.order_book}')
                raise Exception('ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ')
            elif len(step_class_obj.order_book) > 4:
                filtered_list = [order for order in step_class_obj.order_book if order.get('orderType') != 'Limit']
                if len(filtered_list) > 4:
                    custom_logging(bot, f'{step_class_obj.order_book}')
                    raise Exception('len orderbook > 4')

            # Проверка наличия выставленных ордеров
            for position_idx in position_idxs_list:
                if not step_class_obj.ws_checking_opened_new_psn_order(position_idx):
                    step_class_obj.ws_replace_new_psn_order(position_idx)
                else:
                    if step_class_obj.order_missed_check(position_idx):
                        step_class_obj.ws_amend_new_psn_order(position_idx, current_price=True)

            # Снимаем блокировку потока
            if step_class_obj.locker_3.locked():
                step_class_obj.locker_3.release()

            # print(step_class_obj.ws_symbol_list)
            # print()
            sleep_function(10, bot_id)
    except Exception as e:
        custom_logging(bot, f'Error {e}')
        exit_by_exception(bot)

    finally:
        if ws_public and ws_private:
            ws_closing(ws_private, ws_public)
        if is_bot_active(bot_id):
            ActiveBot.objects.filter(bot_id=bot_id).delete()


def ws_closing(*args):
    for ws in args:
        while ws.is_connected():
            ws.exit()
            print('trying to close ws connection')
            time.sleep(1)


def sleep_function(sleep_time, bot_id):
    sleep = 0
    while sleep < sleep_time:
        if is_bot_active(bot_id):
            sleep += 1
            time.sleep(1)
        else:
            break


def manual_average_function(bot, step_hg):
    pass




# def changes_tracking_function(bot, step_hedge, step_class_obj):
#     while ActiveBot.objects.filter(bot_id=bot.pk):
#         apply_changes = False
#         step_hedge_data = StepHedge.objects.get(id=step_hedge.id)
#
#         step_class_obj.short1invest = Decimal(step_hedge_data.short1invest)
#         step_class_obj.long1invest = Decimal(step_hedge_data.long1invest)
#         step_class_obj.margin_short_avg = Decimal(step_hedge_data.margin_short_avg)
#         step_class_obj.margin_long_avg = Decimal(step_hedge_data.margin_long_avg)
#
#         if step_class_obj.tp_pnl_percent != Decimal(step_hedge_data.tp_pnl_percent):
#             step_class_obj.tp_pnl_percent = Decimal(step_hedge_data.tp_pnl_percent)
#             apply_changes = True
#
#         if step_class_obj.pnl_short_avg != Decimal(step_hedge_data.pnl_short_avg):
#             step_class_obj.pnl_short_avg = Decimal(step_hedge_data.pnl_short_avg)
#         if step_class_obj.pnl_long_avg != Decimal(step_hedge_data.pnl_long_avg):
#             step_class_obj.pnl_long_avg = Decimal(step_hedge_data.pnl_long_avg)
#
#         if step_class_obj.qty_steps != step_hedge_data.qty_steps:
#             step_class_obj.qty_steps = step_hedge_data.qty_steps
#             apply_changes = True
#         if step_class_obj.qty_steps_diff != step_hedge_data.qty_steps_diff:
#             step_class_obj.qty_steps_diff = step_hedge_data.qty_steps_diff
#
#         if apply_changes:
#             step_class_obj.locker_3.acquire()
#             cancel_all(step_class_obj.account, step_class_obj.category, step_class_obj.symbol)
#             time.sleep(1)
#
#             # Обновляем книгу ордеров до отмены ордеров
#             status_req_order_book = step_class_obj.update_order_book()
#             if status_req_order_book not in 'OK':
#                 logging(bot, f'ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ -- {step_class_obj.order_book}')
#                 raise Exception('ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ')
#             # Обновляем список позиций
#             step_class_obj.update_symbol_list()
#             if step_class_obj.symbol_list is None:
#                 logging(bot, f'ОШИБКА ПОЛУЧЕНИЯ "SYMBOL LIST"')
#                 raise Exception('ОШИБКА ПОЛУЧЕНИЯ "SYMBOL LIST"')
#
#             for position_number in range(2):
#                 if step_hedge_data.add_tp:
#                     if not step_class_obj.tp_full_size_psn_check(position_number):
#                         if step_class_obj.psn_size_bigger_then_start(position_number):
#                             step_class_obj.add_tp(position_number)
#                         else:
#                             if step_class_obj.checking_opened_position(position_number):
#                                 step_class_obj.place_tp_order(position_number)
#                 else:
#                     if step_class_obj.checking_opened_position(position_number):
#                         step_class_obj.place_tp_order(position_number)
#
#                 if not step_hedge_data.is_nipple_active:
#                     if not step_class_obj.checking_opened_new_psn_order(position_number):
#                         step_class_obj.place_nipple_on_tp(position_number)
#                 else:
#                     if not step_class_obj.checking_opened_new_psn_order(position_number):
#                         step_class_obj.place_new_psn_order(position_number)
#             # Снимаем блокировку потока
#             if step_class_obj.locker_3.locked():
#                 step_class_obj.locker_3.release()
#         time.sleep(4)
