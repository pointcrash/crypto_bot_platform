import logging

from api_2.api_aggregator import get_futures_account_balance, cancel_all_orders, get_all_position_inform
from bots.general_functions import send_telegram_notice
from bots.models import BotModel
from main.models import Account
from orders.models import Position

logger = logging.getLogger('django')


def account_margin_check():
    accounts = Account.objects.all()
    for account in accounts:
        try:
            if account.low_margin_value:
                low_margin = False
                message = 'Маржа опустилась ниже указанного значения'

                balance = get_futures_account_balance(account)
                full_balance = balance['fullBalance']
                available_balance = balance['availableBalance']

                if account.low_margin_value_type == '$':
                    if available_balance < account.low_margin_value:
                        low_margin = True

                elif account.low_margin_value_type == '%':
                    if available_balance < full_balance * account.low_margin_value / 100:
                        low_margin = True

                if low_margin:
                    if account.low_margin_actions == 'alert':
                        send_telegram_notice(account, message)

                    elif account.low_margin_actions == 'off_bots':
                        send_telegram_notice(account, message)

                        bots = BotModel.objects.filter(account=account, is_active=True)
                        bots.update(is_active=False)

                        for bot in bots:
                            cancel_all_orders(bot)
        except Exception as e:
            logger.info(f'{e}')
            continue


def account_positions_check():
    accounts = Account.objects.all()
    for account in accounts:
        try:
            positions = get_all_position_inform(account)
        except Exception as e:
            logger.info(f'{e}')
            continue

        for psn in positions:
            position = Position.objects.filter(
                account=account,
                symbol_name=psn.get('symbol'),
                side=psn.get('side'),
                qty=psn.get('qty'),
                entry_price=psn.get('entryPrice'),
                # unrealised_pnl=psn.get('unrealisedPnl'),
            ).last()

            if position:
                position.unrealised_pnl = psn.get('unrealisedPnl')
                position.save()

            else:
                Position.objects.create(
                    account=account,
                    symbol_name=psn.get('symbol'),
                    side=psn.get('side'),
                    qty=psn.get('qty'),
                    entry_price=psn.get('entryPrice'),
                    unrealised_pnl=psn.get('unrealisedPnl'),
                )
