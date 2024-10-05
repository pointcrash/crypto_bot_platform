# import requests
#
# # bot_token = os.getenv('API_TOKEN')
# bot_token = '2222'
#
#
# def get_data():
#     url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
#     response = requests.get(url)
#     if response.status_code == 200:
#         data = response.json()
#         return data
#     else:
#         raise "Telegram Error fetching updates"
#
#
# def data_username_check(username):
#     data = get_data()
#     for chat_data in data['result']:
#         data_username = chat_data['message']['chat']['username']
#         if data_username == username:
#             return chat_data['message']['chat']
#     raise ValueError('Username not found')
#
#
# def get_chat_id(username):
#     chat_data = data_username_check(username)
#     return chat_data['id']

