import logging
import time

from django.core.cache import cache
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .celery_tasks import run_bot_ws_socket
from .general_functions import custom_user_bot_logging
from .models import BotModel

logger = logging.getLogger('debug_logger')


@receiver(pre_save, sender=BotModel)
def bot_tracking_is_active_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    previous_instance = sender.objects.get(pk=instance.pk)

    if previous_instance.is_active != instance.is_active:
        cache.set(f'bot_{instance.id}_status_changed', True, timeout=60)
        logger.debug('Bot status was change')

        if not instance.is_active:
            custom_user_bot_logging(instance, 'Бот остановлен')

    else:
        if instance.is_active:
            if (previous_instance.leverage, previous_instance.amount_long, previous_instance.amount_short) != \
                    (instance.leverage, instance.amount_long, instance.amount_short):
                logger.debug('Set signal to ws restart')
                cache.set(f'bot_{instance.id}_must_be_restart', True, timeout=60)

        custom_user_bot_logging(instance, 'Данные бота были изменены')


@receiver(post_save, sender=BotModel)
def bot_status_changed(sender, instance, **kwargs):
    if cache.get(f'bot_{instance.id}_status_changed'):
        cache.delete(f'bot_{instance.id}_status_changed')

        if instance.is_active is True:
            logger.debug('Bot status was change to ACTIVE')

            if cache.get(f'close_ws_{instance.id}'):  # Проверяем/удаляем флаг закрытия сокета
                cache.delete(f'close_ws_{instance.id}')  # если такой был установлен

            run_bot_ws_socket.delay(instance.id)  # Отдаем задачу запуска сокета - Селери

        else:
            logger.debug('Bot status was change to UNACTIVE')
            cache.set(f'close_ws_{instance.id}', True, timeout=60)
            logger.debug('Set signal to ws_close')
            custom_user_bot_logging(instance, 'Бот остановлен вручную')

    elif cache.get(f'bot_{instance.id}_must_be_restart'):
        logger.debug(f'bot_{instance.id} socket must be restart')
        cache.delete(f'bot_{instance.id}_must_be_restart')

        cache.set(f'close_ws_{instance.id}', True, timeout=60)

        while cache.get(f'close_ws_{instance.id}'):
            time.sleep(0.3)

        logger.debug(f'bot_{instance.id}socket must be restart run_bot_ws_socket.delay')
        run_bot_ws_socket.delay(instance.id)  # Отдаем задачу запуска сокета - Селери
