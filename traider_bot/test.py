#
# import os
# import django
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
# django.setup()
#
# from main.models import ActiveBot
#
#
# bot_names = list(ActiveBot.objects.values_list('bot_id', flat=True))
# for bot in bot_names:
#     print(bot)