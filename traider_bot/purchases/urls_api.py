from django.urls import path, include
from rest_framework.routers import DefaultRouter

from purchases.vews_api import ServiceProductViewSet, PurchaseViewSet, CreateInvoiceView, PurchasesCallbackView

router = DefaultRouter()
router.register(r'products', ServiceProductViewSet)
router.register(r'purchases', PurchaseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('invoice/create/', CreateInvoiceView.as_view()),
    path('invoice/postback/', PurchasesCallbackView.as_view()),
]
