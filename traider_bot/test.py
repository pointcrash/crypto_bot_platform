import os
import django

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
    django.setup()
    from bots.models import BotModel

    bot = BotModel.objects.get(id=22)
    print(bot.pk)
