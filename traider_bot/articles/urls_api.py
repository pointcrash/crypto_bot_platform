from django.urls import path, include
from rest_framework.routers import DefaultRouter

from articles.views_api import ArticleReadOnlyViewSet, ArticleForAdminViewSet

router = DefaultRouter()
router.register(r'articles', ArticleReadOnlyViewSet, basename='articles')
router.register(r'admin-articles', ArticleForAdminViewSet, basename='admin-articles')

urlpatterns = [
    path('', include(router.urls)),
]
