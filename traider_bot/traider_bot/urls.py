from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from authentication.views import ConfirmEmailView
from bots.views_api import BotModelViewSet, BotReadOnlyViewSet, GridViewSet, BBViewSet, SymbolViewSet
from main.views import logs_list, registration_view, login_view, logout_view, logs_view, view_home, view_logs_delete, \
    profile_list, profile_mode_switching, cleaning_logs_view, user_bot_logs_view
from single_bot.views import say_hello

router = DefaultRouter()
router.register(r'bots', BotModelViewSet, basename='bot')
router.register(r'bots-detail', BotReadOnlyViewSet, basename='bot-detail')
router.register(r'symbols', SymbolViewSet, basename='symbol')

# Вложенный маршрутизатор для bb и grid
bots_router = NestedDefaultRouter(router, r'bots', lookup='bot')
bots_router.register(r'bb', BBViewSet, basename='bot-bb')
bots_router.register(r'grid', GridViewSet, basename='bot-grid')

urlpatterns = [
    path('', view_home, name='home'),
    path('say_hello', say_hello, name='say_hello'),
    path('admin/', admin.site.urls),
    path('logs/', logs_view, name='logs'),
    path('logs/<int:bot_id>/', logs_list, name='logs_detail'),
    path('user_bot_logs/<int:bot_id>/', user_bot_logs_view, name='user_bot_logs'),
    path('cleaning_logs/', cleaning_logs_view, name='cleaning_logs'),
    path('logs/delete/<int:bot_id>/', view_logs_delete, name='logs_delete'),
    path('bots/', include('bots.urls')),
    path('accounts/', include('main.urls')),
    path('single_bot/', include('single_bot.urls')),
    path('bots_group/', include('bots_group.urls')),
    path('telegram/', include('tg_bot.urls')),
    path('orders/', include('orders.urls')),
    path('register/', registration_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_list, name='profile_list'),
    path('profile/profile_mode_switching/<int:profile_id>/', profile_mode_switching, name='profile_mode_switching'),

    path('api/v1/bots/', include('bots.urls_api')),
    path('api/v1/', include('orders.urls_api')),
    path('api/v1/main/', include('main.urls_api')),
    path('api/v1/support/', include('support.urls_api')),
    path('api/v1/documentation/', include('documentation.urls_api')),
    path('api/v1/tariffs/', include('tariffs.urls_api')),
    path('api/v1/', include('purchases.urls_api')),

    path('api/auth/', include('authentication.urls')),
    path('auth/account-confirm-email/<str:key>/', ConfirmEmailView.as_view(), name='front_custom_confirm_email'),
    path('api/v1auth/account-confirm-email/<str:key>/', ConfirmEmailView.as_view(), name='custom_confirm_email'),

    path('api/v1/', include(router.urls)),
    path('api/v1/', include(bots_router.urls)),

    path('allauth/', include('allauth.urls')),
    # path('dj-rest-auth/', include('dj_rest_auth.urls')),
    # path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
]

