# import logging
# import time
#
# from bots.general_functions import update_bots_is_active
# from bots.models import BotModel
#
# logger = logging.getLogger('debug_logger')
#
#
# def initiate_bots_is_running():
#     logger.info(f'Инициализирован запуск ботов')
#     active_bots = BotModel.objects.filter(is_active=True)
#     active_bots.update(is_active=False)
#
#     for bot in active_bots:
#         logger.info(f'Инициализирован запуск бота при старте botid: {bot.id}')
#
#         update_bots_is_active(bot, True)
#         time.sleep(1)
#
#
# if __name__ == '__main__':
#     initiate_bots_is_running()
