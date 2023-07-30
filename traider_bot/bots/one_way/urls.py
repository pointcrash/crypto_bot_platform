from django.urls import path

from bots.one_way.views_grid import one_way_grid_bots_list, one_way_grid_bot_detail, one_way_grid_create_bot

urlpatterns = [
    #
    # path('bb/', one_way_bb_bots_list, name='one_way_bb_bots_list'),
    # path('bb/<int:bot_id>/', one_way_bb_bot_detail, name='one_way_bb_bot_detail'),
    # path('bb/create_bot/', one_way_bb_create_bot, name='one_way_bb_create_bot'),
    #
    path('grid/', one_way_grid_bots_list, name='one_way_grid_bots_list'),
    path('grid/<int:bot_id>/', one_way_grid_bot_detail, name='one_way_grid_bot_detail'),
    path('grid/create_bot/', one_way_grid_create_bot, name='one_way_grid_create_bot'),
    #
]
