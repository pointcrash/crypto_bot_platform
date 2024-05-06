from django.urls import path

from bots.zinger.views import zinger_bot_edit, zinger_bot_create, start_zinger_bot_view

urlpatterns = [
    path('create', zinger_bot_create, name='zinger_bot_create'),
    path('edit/<int:bot_id>', zinger_bot_edit, name='zinger_bot_edit'),
    path('start/<int:bot_id>/<int:event_number>', start_zinger_bot_view, name='start_zinger_bot'),

]