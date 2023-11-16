# import os
#
# import django
#
# from bots.terminate_bot_logic import terminate_thread
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
# django.setup()
#
# from bots.models import Bot
#
#
# def worker_exit(server, worker):
#     all_bots_pks = Bot.objects.values_list('pk', flat=True).order_by('pk')
#     for bot_id in all_bots_pks:
#         print(terminate_thread(bot_id, keep_active=True))
#
#
# def when_ready(server):
#     pass
