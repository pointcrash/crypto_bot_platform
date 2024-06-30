from django.contrib import admin
from django.urls import path, include

from main.views import logs_list, registration_view, login_view, logout_view, logs_view, view_home, view_logs_delete, \
    profile_list, profile_mode_switching, cleaning_logs_view, user_bot_logs_view
from single_bot.views import say_hello
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
# from timezone.views import create_timezone

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

    path('api/v1/', include('bots.urls_api')),
    path('api/v1/main/', include('main.urls_api')),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

]

