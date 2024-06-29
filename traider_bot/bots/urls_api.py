from django.urls import path

from bots.views_api import *

urlpatterns = [

    path('bots/', BotModelViewSet.as_view({'get': 'list'})),
    path('bots/<int:pk>/', BotModelViewSet.as_view({'put': 'update', 'get': 'retrieve', 'delete': 'destroy'})),
    path('bots/account/<int:account_id>/', BotModelViewSet.as_view({'get': 'list_by_account'})),

    path('logs/<int:bot_id>', BotLogsViewSet.as_view({'get': 'list'})),

    path('user_logs/<int:bot_id>', UserBotLogViewSet.as_view({'get': 'list'})),

]
