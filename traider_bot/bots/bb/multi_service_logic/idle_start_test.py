import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()


from binance.client import Client
from bots.bot_logic import is_bot_active
from bots.zinger_vip.logic.start import zinger_vip_worker
from bots.bb.multi_service_logic.start_logic import bb_worker
from main.models import ActiveBot
from bots.models import Bot


def main():
    # bot = Bot.objects.get(pk=543)  # ByBit testnet
    bot = Bot.objects.get(pk=544)  # Binance mainnet
    # client = Client(bot.account.API_TOKEN, bot.account.SECRET_KEY, testnet=False)
    # print(client.futures_create_order(symbol='BTCUSDT', side='BUY', positionSide='LONG', type='MARKET', quantity=0.02))  # Разместить ордер

    if not bot.is_active:
        bot.is_active = True
        bot.save()
    # if not is_bot_active(bot.id):
    #     ActiveBot.objects.create(bot_id=bot.id)
    # bb_worker(bot)
    zinger_vip_worker(bot)


if __name__ == '__main__':
    main()
