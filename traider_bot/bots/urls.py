from django.urls import path

from bots.views_grid import grid_bots_list, grid_bot_detail, grid_create_bot, \
    get_update_symbols_set
from bots.views import bb_create_bot, bb_bots_list, bb_bot_detail, terminate_bot, delete_bot

urlpatterns = [
    path('bb/', bb_bots_list, name='bb_bots_list'),
    path('bb/<int:bot_id>/', bb_bot_detail, name='bb_bot_detail'),
    path('bb/create_bot/', bb_create_bot, name='bb_create_bot'),
    # path('start/<int:bot_id>/', start_bot, name='start_bot'),
    path('terminate/<int:bot_id>/<int:event_number>/', terminate_bot, name='terminate_bot'),
    path('delete/<int:bot_id>/<int:event_number>/<str:redirect_to>', delete_bot, name='delete_bot'),
    #
    path('grid/', grid_bots_list, name='grid_bots_list'),
    path('grid/<int:bot_id>/', grid_bot_detail, name='grid_bot_detail'),
    path('grid/create_bot/', grid_create_bot, name='grid_create_bot'),
    path('update_symbols_set/<str:bot_type>/', get_update_symbols_set, name='get_update_symbols_set'),
]
