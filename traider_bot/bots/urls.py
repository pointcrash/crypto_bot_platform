from django.urls import path

from bots.views import create_bot, bots_list, bot_detail, terminate_bot, delete_bot

urlpatterns = [
    path('', bots_list, name='bots_list'),
    path('<int:bot_id>/', bot_detail, name='bot_detail'),
    path('create_bot/', create_bot, name='create_bot'),
    # path('start/<int:bot_id>/', start_bot, name='start_bot'),
    path('terminate/<int:bot_id>/<int:event_number>/', terminate_bot, name='terminate_bot'),
    path('delete/<int:bot_id>/<int:event_number>/', delete_bot, name='delete_bot'),
]
