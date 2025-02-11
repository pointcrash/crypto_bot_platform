from tg_bot.models import TelegramAccount
from tg_bot.send_message import send_telegram_message


def exception_telegram_notice_decorator(message):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                bot_or_account = kwargs.get('bot') or (args[0] if args else None)

                if not bot_or_account or not hasattr(bot_or_account, 'owner'):
                    bot_or_account = kwargs.get('account') or (args[0] if args else None)

                    if not bot_or_account or not hasattr(bot_or_account, 'owner'):
                        raise Exception('incorrect bot_or_account')

                owner = bot_or_account.owner

                tg_acc = TelegramAccount.objects.filter(owner=owner).first()

                if hasattr(bot_or_account, 'account'):
                    pre_message = f'Account: {bot_or_account.account.name}\nBot: {bot_or_account.id}\nSymbol: {bot_or_account.symbol}\n'
                else:
                    pre_message = f'Account: {bot_or_account.name}\n'

                post_message = f'\n\n{e}'

                send_telegram_message(
                    tg_acc.chat_id,
                    message=pre_message + message + post_message,
                )

                raise Exception(e)
        return wrapper
    return decorator
