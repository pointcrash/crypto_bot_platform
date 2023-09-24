# import os
# import django
#
# from api_v5 import get_list, get_open_orders
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
# django.setup()
#
# from bots.models import Bot
# from main.models import Account
#
# bot = Bot.objects.get(pk=404)
# acc = Account.objects.get(pk=1)
# print(get_open_orders(bot=bot))
i = dict()
i[1] = 'dfsd'
i[2] = ''
for w in range(1, 3):
    if i[w]:
        print(i[w])
