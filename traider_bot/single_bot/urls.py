from django.urls import path

from bots.SimpleHedge.views import simple_hedge_bot_create
from bots.one_way.views_bb import single_bb_bot_create, single_bb_bot_detail
from single_bot.views import single_bot_list, single_bot_detail, single_bot_create, bot_start

urlpatterns = [
    path('', single_bot_list, name='single_bot_list'),
    path('grid/create/', single_bot_create, name='single_bot_create'),
    path('bb/create/', single_bb_bot_create, name='single_bb_bot_create'),
    path('grid/detail/<int:bot_id>', single_bot_detail, name='single_bot_detail'),
    path('bb/detail/<int:bot_id>', single_bb_bot_detail, name='single_bb_bot_detail'),
    path('start/<int:bot_id>', bot_start, name='single_bot_start'),

    path('simple_hedge/create/', simple_hedge_bot_create, name='simple_hedge_bot_create'),
    # path('grid/detail/<int:bot_id>', single_bot_detail, name='single_bot_detail'),
]
