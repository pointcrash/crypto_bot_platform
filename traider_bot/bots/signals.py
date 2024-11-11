import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .bb.logic.start_logic import bb_bot_ws_connect
from .global_variables import bot_id_ws_clients
from .models import BotModel

logger = logging.getLogger('debug_logger')


@receiver(pre_save, sender=BotModel)
def bot_tracking_is_active_change(sender, instance, **kwargs):
    previous_instance = sender.objects.get(pk=instance.pk)

    if previous_instance.is_active != instance.is_active:
        if instance.is_active is True:
            if instance.work_model == 'bb':
                ws_client = bb_bot_ws_connect(instance)
                bot_id_ws_clients[instance.pk] = ws_client

            elif instance.work_model == 'grid':
                pass

        if instance.is_active is False:
            ws_clint = bot_id_ws_clients.pop(instance.pk)
            ws_clint.exit()
