from django.urls import path

from bots.bb.views import bb_bot_create, bb_bot_edit

urlpatterns = [
    path('create', bb_bot_create, name='bb_bot_create'),
    path('edit/<int:bot_id>', bb_bot_edit, name='bb_bot_edit'),

]