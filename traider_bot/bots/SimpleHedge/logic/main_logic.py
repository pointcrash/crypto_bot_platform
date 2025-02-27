import time

from bots.SimpleHedge.logic.smp_bot_class import SimpleHedgeClassLogic
from bots.general_functions import lock_release, custom_logging, exit_by_exception
from single_bot.logic.global_variables import lock, global_list_bot_id


def simple_hedge_bot_main_logic(bot, smp_hg):
    bot_id = bot.pk
    smp_class_obj = SimpleHedgeClassLogic(bot, smp_hg)

    # Выполняем подготовительные действия для старта работы бота
    smp_class_obj.preparatory_actions()

    # Проверяем имеются ли открытые позиции
    if not smp_class_obj.checking_opened_positions():
        # Проверяем указана ли точка входа и закупаемся
        if bot.price:
            smp_class_obj.buy_by_limit()
        else:
            smp_class_obj.buy_by_market()

    # smp_class_obj.calc_first_order_qty()
    # Запускаем цикл отслеживания состояния позиций
    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            lock_release()

            # Обновляем книгу ордеров до отмены ордеров
            status_req_order_book = smp_class_obj.update_order_book()
            if status_req_order_book not in 'OK':
                custom_logging(bot, f'ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ -- {smp_class_obj.order_book}')
                raise Exception('ОШИБКА ПОЛУЧЕНИЯ СПИСКА ОРДЕРОВ')
            # Обновляем список позиций
            smp_class_obj.update_symbol_list()
            if smp_class_obj.symbol_list is None:
                custom_logging(bot, f'ОШИБКА ПОЛУЧЕНИЯ "SYMBOL LIST"')
                raise Exception('ОШИБКА ПОЛУЧЕНИЯ "SYMBOL LIST"')

            # # Проверяем равенство цен открытых позиций
            # difference_price = smp_class_obj.psn_price_difference_calculation()
            # if difference_price:
            #     if not smp_class_obj.order_equalize_check():
            #         # Если разница есть - уравниваем цены
            #         smp_class_obj.equalize_positions_price(difference_price)
            #     time.sleep(10)
            #     continue
            #
            # smp_class_obj.cancel_equalize_orders()

            for position_number in range(2):
                time.sleep(1)
                # Статус позиции принимает значения " >, <, = " или "Error"
                position_status = smp_class_obj.take_position_status(position_number)

                time.sleep(1)

                if position_status == 'Error':
                    custom_logging(bot, f'ОДНА ИЛИ ОБЕ ПОЗИЦИИ РАВНЫ 0 -- {smp_class_obj.symbol_list}')
                    raise Exception(f'ОДНА ИЛИ ОБЕ ПОЗИЦИИ РАВНЫ 0 -- {smp_class_obj.symbol_list}')

                elif position_status == '>':
                    time.sleep(1)
                    if not smp_class_obj.checking_opened_order(position_number):
                        smp_class_obj.higher_position(position_number)

                elif position_status == '<':
                    time.sleep(1)
                    order = smp_class_obj.checking_opened_order_for_lower_psn(position_number)
                    if not order or smp_class_obj.checking_change_qty_for_order_lower_psn(position_number, order):
                        time.sleep(1)
                        smp_class_obj.lower_position(position_number)

                elif position_status == '=':
                    if smp_class_obj.add_psn_flag[position_number] is True:
                        smp_class_obj.cancel_tp_orders(position_number)
                        smp_class_obj.add_psn_flag[position_number] = False

                    time.sleep(1)
                    if not smp_class_obj.checking_opened_order(position_number):
                        for count in range(smp_hg.tp_count):
                            count += 1
                            response_equal = smp_class_obj.equal_position(position_number, count)
                            if response_equal['retMsg'] != 'OK':
                                smp_class_obj.sale_at_better_price(position_number)

            time.sleep(3)
            lock.acquire()
    except Exception as e:
        custom_logging(bot, f'Error {e}')
        lock.acquire()
        try:
            exit_by_exception(bot)
        finally:
            lock_release()
    finally:
        lock_release()
