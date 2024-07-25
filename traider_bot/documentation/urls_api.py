from django.urls import path, include
from rest_framework.routers import DefaultRouter

from documentation.vews_api import *

router = DefaultRouter()
router.register(r'doc-page', DocPageReadOnlyViewSet, basename='doc-page')
router.register(r'admin-doc-page', DocPageForAdminViewSet, basename='admin-doc-page')
router.register(r'tag', DocTagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
