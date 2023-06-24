from django.urls import path

from bots.views import create_bot, bots_list, bot_detail

urlpatterns = [
    path('', bots_list, name='bots_list'),
    path('<int:bot_id>/', bot_detail, name='bot_detail'),
    path('create_bot/', create_bot, name='create_bot'),
]
