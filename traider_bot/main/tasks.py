from api_2.api_aggregator import get_futures_account_balance
from bots.general_functions import send_telegram_notice
from bots.models import BotModel
from main.models import Account


def account_margin_check():
    accounts = Account.objects.all()
    for account in accounts:
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
                    BotModel.objects.filter(account=account, is_active=True).update(is_active=False)

