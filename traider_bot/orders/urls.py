from django.urls import path

from orders.views import *

urlpatterns = [
    path('create/<int:bot_id>/', place_custom_order_view, name='create_order'),
    path('cancel/<int:bot_id>/<str:order_id>/', cancel_selected_order_view, name='cancel_selected_order'),
    path('close/position/<int:bot_id>/<str:psn_side>/<str:qty>/', close_selected_position_view, name='close_selected_position'),
]
