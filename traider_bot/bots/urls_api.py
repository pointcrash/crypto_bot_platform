from django.urls import path

from bots.views_api import *

urlpatterns = [
    path('logs/<int:bot_id>', BotLogsViewSet.as_view({'get': 'list'})),
    path('user_logs/<int:bot_id>', UserBotLogViewSet.as_view({'get': 'list'})),

    path('by-account/<int:account_id>/', BotReadOnlyViewSet.as_view({'get': 'list_by_account'})),

]
