if __name__ == '__main__':
    import os
    import requests
    import telebot

    API_TOKEN = os.getenv('API_TOKEN')
    MAIN_SERVER_URL = os.getenv('MAIN_SERVER_URL')
    bot = telebot.TeleBot(API_TOKEN)


    @bot.message_handler(commands=['start'])
    def handle_start(message):
        chat_id = message.chat.id
        username = message.from_user.username if message.from_user.username else 'have not username'
        bot.send_message(chat_id, f"Привет, я ваш телеграм-бот!")

        user_id = message.text.split()[1] if len(message.text.split()) > 1 else None
        if user_id:
            url = 'https://' + MAIN_SERVER_URL + '/api/v1/tg/bot-connect/'
            data = {
                "chat_id": message.chat.id,
                "username": username,
                "user_id": user_id
            }
            response = requests.post(url, data=data)
            if response.status_code == 200:
                bot.send_message(chat_id, "Подключение прошло успешно! Пожалуйста, обновите страницу.")
            else:
                bot.send_message(chat_id, f"Ошибка отправки данных: {response.status_code}, {response.text}")
        else:
            bot.send_message(chat_id, "Привет! Вы не отправили параметров.")

    bot.polling()
