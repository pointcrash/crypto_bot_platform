import logging
import time
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone

from api_2.api_aggregator import get_futures_account_balance, cancel_all_orders, get_all_position_inform, \
    transaction_history
from bots.general_functions import send_telegram_notice, all_symbols_update, custom_logging, custom_user_bot_logging
from bots.models import BotModel, Symbol
from main.models import Account, AccountBalance, AccountHistory
from main.tests import generate_date_ranges, convert_timestamp_to_datetime
from orders.models import Position
from tariffs.models import UserTariff
from decimal import Decimal, ROUND_HALF_UP

from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message

logger = logging.getLogger('django')


def account_margin_check():
    accounts = Account.objects.all()
    for account in accounts:
        try:
            if not account.margin_alert_is_active:
                continue

            if account.low_margin_value:
                low_margin = False
                message = 'Маржа опустилась ниже указанного значения'

                balance = get_futures_account_balance(account)
                full_balance = balance['fullBalance']
                available_balance = balance['availableBalance']

                if account.low_margin_value_type == '$':
                    if available_balance < account.low_margin_value:
                        low_margin = True
                        message += f'\n Указанное значение - {account.low_margin_value}{account.low_margin_value_type}'
                        message += f'\n Доступный баланс - {available_balance}$'

                elif account.low_margin_value_type == '%':
                    if available_balance < full_balance * account.low_margin_value / 100:
                        low_margin = True
                        message += f'\n Указанное значение - {account.low_margin_value}{account.low_margin_value_type}'
                        message += f'\n Полный баланс - {full_balance}$'
                        message += f'\n Доступный баланс - {available_balance}$'

                if low_margin:
                    if account.low_margin_actions == 'alert':
                        send_telegram_notice(account, message)

                    elif account.low_margin_actions == 'off_bots':
                        send_telegram_notice(account, message)

                        bots = BotModel.objects.filter(account=account, is_active=True)
                        # bots.update(is_active=False)

                        for bot in bots:
                            cancel_all_orders(bot)
                            bot.is_active = False
                            bot.save()

        except Exception as e:
            # logger.info(f'{e}')
            continue


def account_positions_check():
    accounts = Account.objects.all()
    for account in accounts:
        try:
            positions = get_all_position_inform(account)
        except Exception as e:
            # logger.info(f'{e}')
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


def account_balance_history_update():
    accounts = Account.objects.all()
    for account in accounts:

        current_day = date.today()
        if AccountBalance.objects.filter(account=account, time_create__date=current_day).first():
            continue

        try:
            balance_data = get_futures_account_balance(account)
            AccountBalance.objects.create(
                account=account,
                asset='USDT',
                balance=balance_data['fullBalance'],
                available_balance=balance_data['availableBalance'],
                un_pnl=balance_data['unrealizedPnl'],
            )
        except Exception as e:
            logger.error(f"Ошибка получения баланса для аккаунта {account.name}. Ошибка: {e}")
            AccountBalance.objects.create(account=account)

        time.sleep(3)


def get_account_transaction_history():
    accounts = Account.objects.all()
    for account in accounts:
        try:
            acc_history_last = AccountHistory.objects.filter(account=account).last()
            start_time = acc_history_last.transaction_time if acc_history_last else None
            date_ranges = generate_date_ranges(start_time) if start_time else generate_date_ranges()

            for date in date_ranges:
                history_data = transaction_history(account, start_time=date[0], end_time=date[1])

                account_history_objects = [
                    AccountHistory(
                        account=account,
                        symbol=transaction.get('symbol'),
                        side=transaction.get('side'),
                        order_id=transaction.get('orderId'),
                        change=transaction.get('change'),
                        cash_flow=transaction.get('cashFlow'),
                        fee=transaction.get('fee'),
                        transaction_time=convert_timestamp_to_datetime(transaction.get('transactionTime')),
                        type=transaction.get('type'),
                    ) for transaction in history_data
                ]

                AccountHistory.objects.bulk_create(account_history_objects)

        except Exception as e:
            logger.error(f"Ошибка получения истории для аккаунта {account.name}. Ошибка: {e}")


def auto_symbols_update():
    all_symbols_update()


def expiration_time_update():
    user_tariffs = UserTariff.objects.all()

    for tariff in user_tariffs:
        if not tariff.expiration_time:
            tariff.expiration_time = tariff.created_at + timedelta(days=30)

    UserTariff.objects.bulk_update(user_tariffs, ['expiration_time'])


def rounding_margin_from_account_balances():
    account_balances = AccountBalance.objects.all()
    for ac_b in account_balances:
        if ac_b.margin:
            ac_b.margin = str(Decimal(ac_b.margin).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            ac_b.save()


def bots_alive_check():
    bot_id_need_to_deactivate = []
    bot_id_need_to_activate = []
    bots = BotModel.objects.all()
    pattern = 'ws-*-q-*'
    keys = cache.keys(pattern)

    active_bot_id_list = [int((next(x for x in key.split('-') if x.isdigit()))) for key in keys]
    logger.info(f'active_bot_id_list-{active_bot_id_list}')

    for bot in bots:

        if bot.is_active and bot.id not in active_bot_id_list:
            logger.info(f'BOT-{bot.id} is active and not in active_bot_id_list: {active_bot_id_list}')
            bot_id_need_to_deactivate.append(bot.id)

        elif not bot.is_active and bot.id in active_bot_id_list:
            logger.info(f'BOT-{bot.id} is not active but in active_bot_id_list: {active_bot_id_list}')
            bot_id_need_to_activate.append(bot.id)

    if bot_id_need_to_deactivate:
        bots_to_deactivate = BotModel.objects.filter(pk__in=bot_id_need_to_deactivate)

        for bot in bots_to_deactivate:
            if bot.restart_try is False:
                bot.is_active = False
                bot.conn_status = False
                bot.save(update_fields=['is_active', 'conn_status'])

            else:
                bot.is_active = False
                bot.conn_status = False
                bot.forcibly_stopped = True
                bot.save(update_fields=['is_active', 'conn_status', 'forcibly_stopped'])

                message = "WebSocket connection was lost"
                custom_logging(bot, message)
                custom_user_bot_logging(bot, message)

        # BotModel.objects.filter(pk__in=bot_id_need_to_deactivate).update(is_active=False, conn_status=False)

    if bot_id_need_to_activate:
        BotModel.objects.filter(pk__in=bot_id_need_to_activate).update(is_active=True, conn_status=True)


def emergency_launch_bots():
    bots = BotModel.objects.all()

    for bot in bots:
        if bot.enabled_manually and not bot.is_active and not bot.forcibly_stopped:
            bot.is_active = True
            bot.restart_try = True
            bot.save(update_fields=['is_active', 'restart_try'])


def user_tariffs_check():
    users = User.objects.all()
    for user in users:
        user_tariff = UserTariff.objects.filter(user=user).order_by('-created_at').first()

        if not user_tariff:
            continue

        if user_tariff.tariff.title != 'Guest':
            if timezone.now() > user_tariff.expiration_time:
                user_bots = BotModel.objects.filter(owner=user)

                for bot in user_bots:
                    bot.is_active = False
                    bot.save()

            elif user_tariff.expiration_time - timezone.now() < timedelta(days=7):
                tg_acc = TelegramAccount.objects.filter(owner=user).first()
                if tg_acc:
                    remaining_time = user_tariff.expiration_time - timezone.now()
                    days = remaining_time.days

                    message = f'Your tariff expires in {days} days.'

                    send_telegram_message(
                        tg_acc.chat_id,
                        message=message,
                    )


def min_notional_for_all_symbols():
    Symbol.objects.all().update(min_notional='5')


def change_all_test_accounts_to_demo():
    accounts = Account.objects.all()

    for account in accounts:
        if account.is_demonet is True:
            account.is_mainnet = False
            account.save(update_fields=['is_mainnet'])
