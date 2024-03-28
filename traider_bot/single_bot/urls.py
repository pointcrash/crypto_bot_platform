from django.urls import path

from bots.SimpleHedge.views import simple_hedge_bot_create, simple_hedge_bot_detail
from bots.StepHedge.views import step_hedge_bot_create, step_hedge_bot_detail
from bots.one_way.views_bb import single_bb_bot_create, single_bb_bot_detail
from single_bot.views import single_bot_detail, single_bot_create

urlpatterns = [
    # path('list/', single_bot_list, name='single_bot_list'),
    path('grid/create/', single_bot_create, name='single_bot_create'),
    path('bb/create/', single_bb_bot_create, name='single_bb_bot_create'),
    path('grid/detail/<int:bot_id>', single_bot_detail, name='single_bot_detail'),
    path('bb/detail/<int:bot_id>', single_bb_bot_detail, name='single_bb_bot_detail'),

    path('simple_hedge/create/', simple_hedge_bot_create, name='simple_hedge_bot_create'),
    path('simple_hedge/detail/<int:bot_id>', simple_hedge_bot_detail, name='simple_hedge_bot_detail'),
    path('step_hedge/create/', step_hedge_bot_create, name='step_hedge_bot_create'),
    path('step_hedge/detail/<int:bot_id>', step_hedge_bot_detail, name='step_hedge_bot_detail'),
]
