from django.urls import path

from tg_bot.views import telegram_add_account, telegram_list, delete_tg_acc, say_hello

urlpatterns = [
    path('', telegram_list, name='telegram_list'),
    path('add/', telegram_add_account, name='telegram_add_account'),
    path('delete/', delete_tg_acc, name='delete_tg_acc'),
    path('say_hello/', say_hello, name='say_hello'),

]
