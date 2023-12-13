from django.urls import path

from bots_group.views import *

urlpatterns = [
    path('list/', bots_groups_list, name='bots_groups_list'),
    path('step_hedge/create/', group_step_hedge_bot_create, name='group_step_hedge_bot_create'),
    # path('step_hedge/detail/<int:bot_id>', step_hedge_bot_detail, name='step_hedge_bot_detail'),
    path('stop_group/<int:group_id>', stop_group, name='stop_group'),
    path('delete_group/<int:group_id>', delete_group, name='delete_group'),
]
