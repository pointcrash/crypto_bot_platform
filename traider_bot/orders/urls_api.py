from django.urls import path

from orders.views_api import PositionViewSet

urlpatterns = [
    path('positions/', PositionViewSet.as_view({'get': 'list_by_bots'})),

]
