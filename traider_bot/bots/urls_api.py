from django.urls import path

from bots.views_api import *

urlpatterns = [

    # path('', BotModelViewSet.as_view({'get': 'list'})),
    # path('<int:pk>/', BotModelViewSet.as_view({'put': 'update', 'get': 'retrieve', 'delete': 'destroy'})),
    # path('account/<int:account_id>/', BotModelViewSet.as_view({'get': 'list_by_account'})),

    path('logs/<int:bot_id>', BotLogsViewSet.as_view({'get': 'list'})),

    path('user_logs/<int:bot_id>', UserBotLogViewSet.as_view({'get': 'list'})),

    # path('start/<int:bot_id>/', bot_start, name='api_bot_start'),
    # path('terminate/<int:bot_id>/<int:event_number>/', stop_bot, name='api_terminate_bot'),
    # path('delete/<int:bot_id>/<int:event_number>/', delete_bot, name='api_delete_bot'),
    # path('deactivate/all/my/bots/', deactivate_all_my_bots, name='api_deactivate_all_my_bots'),
]
