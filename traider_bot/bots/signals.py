import logging

from django.core.cache import cache
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .celery_tasks import run_bot_ws_socket
from .models import BotModel

logger = logging.getLogger('debug_logger')


@receiver(pre_save, sender=BotModel)
def bot_tracking_is_active_change(sender, instance, **kwargs):
    previous_instance = sender.objects.get(pk=instance.pk)

    if previous_instance.is_active != instance.is_active:
        cache.set(f'bot_{instance.id}_status_changed', True, timeout=60)
        logger.debug('Bot status was change')


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
