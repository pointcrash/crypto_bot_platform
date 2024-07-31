from django.urls import path, include
from rest_framework.routers import DefaultRouter

from tariffs.vews_api import UserTariffViewSet, TariffReadOnlyViewSet

router = DefaultRouter()
router.register(r'list', TariffReadOnlyViewSet)
router.register(r'users', UserTariffViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('by-user-id/<int:user_id>/', UserTariffViewSet.as_view({'get': 'list_by_user_id'})),
]
