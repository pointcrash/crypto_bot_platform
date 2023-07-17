from django.urls import path

from bots.hedge.views_grid import hedge_grid_bots_list, hedge_grid_create_bot, hedge_grid_bot_detail

urlpatterns = [
    path('grid/list', hedge_grid_bots_list, name='hedge_grid_list'),
    path('grid/create', hedge_grid_create_bot, name='hedge_grid_create'),
    path('grid/detail/<int:bot_id>', hedge_grid_bot_detail, name='hedge_grid_detail'),
]
