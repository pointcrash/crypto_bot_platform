from django.urls import path

from orders.views_api import PositionViewSet, CancelOrderView, PlaceManualOrderView, GetOrdersHistoryByTimeView

urlpatterns = [
    path('positions/', PositionViewSet.as_view({'get': 'list_by_bots'})),
    path('orders/cancel-order/<int:bot_id>/<str:order_id>/', CancelOrderView.as_view()),
    path('orders/place-order/', PlaceManualOrderView.as_view()),
    path('orders/history/by-time/', GetOrdersHistoryByTimeView.as_view()),
]
