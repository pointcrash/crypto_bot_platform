from django.urls import path

from orders.views_api import PositionViewSet, CancelOrderView

urlpatterns = [
    path('positions/', PositionViewSet.as_view({'get': 'list_by_bots'})),
    path('orders/cancel-order/<int:order_pk>/', CancelOrderView.as_view()),

]
