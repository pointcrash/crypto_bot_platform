import os
import django

from api_2.api_aggregator import get_position_inform

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')
django.setup()

from bots.bot_logic import is_bot_active
from bots.zinger_vip.logic.start import zinger_vip_worker
from bots.bb.multi_service_logic.start_logic import bb_worker
from main.models import ActiveBot
from bots.models import Bot


def main():
    bot = Bot.objects.get(pk=543)  # ByBit testnet
    # bot = Bot.objects.get(pk=544)  # Binance mainnet

    if not is_bot_active(bot.id):
        ActiveBot.objects.create(bot_id=bot.id)
    # bb_worker(bot)
    # zinger_vip_worker(bot)
    print(get_position_inform(bot))


if __name__ == '__main__':
    main()
