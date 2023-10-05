import requests
from .connect_tg_bot import bot_token


def send_telegram_message(chat_id, bot=None,  message='None'):
    bot_info = f'Bot {bot.pk} - {bot}' if bot else ''
    message = bot_info + ': ' + message if bot else message
    c = 0
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    while c < 10:
        c += 1
        response = requests.post(url, json=data)

        if response.status_code == 200:
            break
        else:
            continue

