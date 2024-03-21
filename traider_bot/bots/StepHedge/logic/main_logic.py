import time

from bots.StepHedge.logic.step_hg_class import StepHedgeClassLogic
from bots.bot_logic import lock_release, custom_logging, exit_by_exception
from main.models import ActiveBot
from single_bot.logic.global_variables import lock, global_list_bot_id


def step_hedge_bot_main_logic(bot, step_hg):
    bot_id = bot.pk
    step_class_obj = StepHedgeClassLogic(bot, step_hg)
    # bot_names = list(ActiveBot.objects.values_list('bot_id', flat=True))

    # Выполняем подготовительные действия для старта работы бота
    step_class_obj.preparatory_actions()

    # Проверяем имеются ли открытые позиции
    if not step_class_obj.checking_opened_positions():
        # Проверяем указана ли точка входа и закупаемся
        if bot.price:
            step_class_obj.buy_by_limit()
        else:
            step_class_obj.buy_by_market()
            # step_class_obj.buy_by_market_limit_order()

    # Запускаем цикл отслеживания состояния позиций
    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            lock_release()

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

            time.sleep(7)
            # bot_names = list(ActiveBot.objects.values_list('name', flat=True))

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
