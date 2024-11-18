from django.urls import path

from bots.views_api import *

urlpatterns = [
    path('<int:bot_id>/logs/', BotLogsViewSet.as_view({'get': 'list', 'delete': 'delete_all_logs_by_bot'})),
    path('<int:bot_id>/user_logs/', UserBotLogViewSet.as_view({'get': 'list', 'delete': 'delete_all_logs_by_bot'})),
    path('delete_all_logs_danger/', BotLogsViewSet.as_view({'get': 'delete_all_logs'})),

    path('by-account/<int:account_id>/', BotReadOnlyViewSet.as_view({'get': 'list_by_account'})),
    path('by-user/<int:user_id>/', BotReadOnlyViewSet.as_view({'get': 'list_by_user_id'})),

    path('start/<int:bot_id>/', BotStartView.as_view(), name='start_bot'),
    path('terminate/<int:bot_id>/<int:event_number>/', StopBotView.as_view(), name='stop_bot'),
    path('delete/<int:bot_id>/<int:event_number>/', DeleteBotView.as_view(), name='delete_bot'),
    path('deactivate/all/my/bots/', DeactivateAllMyBotsView.as_view(), name='deactivate_all_bots'),

    path('<int:bot_id>/get-positions-orders/', GetOrdersAndPositionsHistoryBotsView.as_view(), name='get_positions_orders'),
    path('<int:bot_id>/close-position/', CloseSelectedPositionView.as_view(), name='close_position_by_bot'),
]
