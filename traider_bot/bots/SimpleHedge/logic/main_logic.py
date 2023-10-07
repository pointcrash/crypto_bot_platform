import time

from bots.SimpleHedge.logic.smp_bot_class import SimpleHedgeClassLogic
from bots.bot_logic import lock_release
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

    # Запускаем цикл отслеживания состояния позиций
    lock.acquire()
    try:
        while bot_id in global_list_bot_id:
            lock_release()

            # Обновляем книгу ордеров до отмены ордеров
            smp_class_obj.update_order_book()
            # Обновляем список позиций
            smp_class_obj.update_symbol_list()

            for position_number in range(2):
                if not smp_class_obj.checking_opened_order(position_number):

                    # Статус позиции принимает значения " >, <, = "
                    position_status = smp_class_obj.take_position_status(position_number)

                    if position_status == '>':
                        smp_class_obj.higher_position(position_number)
                    elif position_status == '<':
                        smp_class_obj.lower_position(position_number)
                    else:
                        smp_class_obj.equal_position(position_number)

            time.sleep(5)
            lock.acquire()
    # except Exception as e:
    #     logging(bot, f'Error {e}')
    #     lock.acquire()
    #     try:
    #         exit_by_exception(bot)
    #     finally:
    #         lock_release()
    finally:
        lock_release()

