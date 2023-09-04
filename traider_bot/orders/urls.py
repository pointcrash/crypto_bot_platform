from django.urls import path
from orders.views import create_order_view, cancel_order_view

urlpatterns = [
    path('create/<int:bot_id>/', create_order_view, name='create_order'),
    path('cancel/<int:bot_id>/<str:order_id>/', cancel_order_view, name='cancel_order'),
]
