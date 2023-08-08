import requests


def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print("Сообщение отправлено успешно")
    else:
        print("Ошибка при отправке сообщения")


# Замените на свой токен и чат-идентификатор
bot_token = "ВАШ_ТОКЕН"
chat_id = "ВАШ_ЧАТ_ИДЕНТИФИКАТОР"
message_text = "Привет, это ваше уведомление из Python!"

send_telegram_message(bot_token, chat_id, message_text)
