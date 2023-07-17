from django.contrib import admin
from django.urls import path, include

from main.views import logs_list, registration_view, login_view, logout_view, logs_view, view_home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logs/', logs_view, name='logs'),
    path('logs/<int:bot_id>/', logs_list, name='logs_detail'),
    path('bots/', include('bots.urls')),
    path('accounts/', include('main.urls')),
    path('register/', registration_view, name='register'),
    path('', login_view, name='login'),
    path('home/', view_home, name='home'),
    path('logout/', logout_view, name='logout'),
]
