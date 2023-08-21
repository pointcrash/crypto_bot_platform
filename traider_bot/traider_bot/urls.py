from django.contrib import admin
from django.urls import path, include

from main.views import logs_list, registration_view, login_view, logout_view, logs_view, view_home, view_logs_delete, \
    profile_list, profile_mode_switching
# from timezone.views import create_timezone

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('set_timezones/', create_timezone, name='create_timezone'),
    path('logs/', logs_view, name='logs'),
    path('logs/<int:bot_id>/', logs_list, name='logs_detail'),
    path('logs/delete/<int:bot_id>/', view_logs_delete, name='logs_delete'),
    path('bots1/', include('bots.urls')),
    path('accounts/', include('main.urls')),
    path('bots/', include('single_bot.urls')),
    path('telegram/', include('tg_bot.urls')),
    path('register/', registration_view, name='register'),
    path('login/', login_view, name='login'),
    path('home/', view_home, name='home'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_list, name='profile_list'),
    path('profile/profile_mode_switching/<int:profile_id>/', profile_mode_switching, name='profile_mode_switching'),

]
