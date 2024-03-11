from django.urls import path

from bots.bb.views import bb_bot_create

urlpatterns = [
    path('bot_create/', bb_bot_create, name='bb_bot_create'),

]