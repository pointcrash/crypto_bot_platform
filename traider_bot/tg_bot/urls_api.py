from rest_framework.routers import DefaultRouter
from django.urls import path, include

from tg_bot.views_api import TelegramAccountViewSet, TelegramSayHelloView, BotConnectView, \
    BotDisconnectView

router = DefaultRouter()
router.register(r'telegram_account', TelegramAccountViewSet, basename='telegram_account')

urlpatterns = [
    path('', include(router.urls)),
    path('tg/say-hello/', TelegramSayHelloView.as_view(), name='tg_say_hello'),
    # path('tg/delete-account/', TelegramAccountDeleteView.as_view(), name='tg_delete_account'),
    path('tg/bot-connect/', BotConnectView.as_view(), name='tg_bot_connect'),
    path('tg/bot-disconnect/', BotDisconnectView.as_view(), name='tg_bot_disconnect'),
]
