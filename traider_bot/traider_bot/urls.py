from django.contrib import admin
from django.urls import path, include

from main.views import logs_list, registration_view, login_view, logout_view, logs_view, view_home, view_logs_delete, \
    profile_list, profile_mode_switching, cleaning_logs_view

# from timezone.views import create_timezone

urlpatterns = [
    path('', view_home, name='home'),
    path('admin/', admin.site.urls),
    path('logs/', logs_view, name='logs'),
    path('logs/<int:bot_id>/', logs_list, name='logs_detail'),
    path('cleaning_logs/', cleaning_logs_view, name='cleaning_logs'),
    path('logs/delete/<int:bot_id>/', view_logs_delete, name='logs_delete'),
    path('bots1/', include('bots.urls')),
    path('accounts/', include('main.urls')),
    path('bots/', include('single_bot.urls')),
    path('telegram/', include('tg_bot.urls')),
    path('orders/', include('orders.urls')),
    path('register/', registration_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_list, name='profile_list'),
    path('profile/profile_mode_switching/<int:profile_id>/', profile_mode_switching, name='profile_mode_switching'),

]
