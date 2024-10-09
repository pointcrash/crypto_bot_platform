from django.urls import path, include
from rest_framework.routers import DefaultRouter

from purchases.vews_api import ServiceProductViewSet, PurchaseViewSet, create_invoice_view, purchases_callback_view

router = DefaultRouter()
router.register(r'products', ServiceProductViewSet)
router.register(r'purchases', PurchaseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('create_invoice/', create_invoice_view, name='create_invoice'),
    path('purchases/callback/', purchases_callback_view, name='purchases_callback'),
]
