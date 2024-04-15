from datetime import datetime, timedelta
import pytz
from bots.models import Log
from timezone.models import TimeZone


def custom_logging(bot, text, named=None):
    user = bot.owner
    timezone = TimeZone.objects.filter(users=user).first()
    gmt0 = pytz.timezone('GMT')
    date = datetime.now(gmt0).replace(microsecond=0)
    bot_info = f'Bot {bot.pk} {bot.symbol.name}'
    gmt = 0

    if timezone:
        gmt = int(timezone.gmtOffset)
        if gmt > 0:
            date = date + timedelta(seconds=gmt)
        else:
            date = date - timedelta(seconds=gmt)

    if gmt > 0:
        str_gmt = '+' + str(gmt / 3600)
    elif gmt < 0:
        str_gmt = str(gmt / 3600)
    else:
        str_gmt = str(gmt)

    in_time = f'{date.time()} | {date.date()}'
    if named:
        Log.objects.create(bot=bot, content=f'{bot_info} {named} {text}', time=f'{in_time} (GMT {str_gmt})')
    else:
        Log.objects.create(bot=bot, content=f'{bot_info} {text}', time=f'{in_time} (GMT {str_gmt})')
