from django.urls import path

from bots.zinger.views import zinger_bot_edit, zinger_bot_create

urlpatterns = [
    path('create', zinger_bot_create, name='zinger_bot_create'),
    path('edit/<int:bot_id>', zinger_bot_edit, name='zinger_bot_edit'),

]