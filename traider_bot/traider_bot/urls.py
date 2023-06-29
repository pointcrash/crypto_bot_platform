from django.contrib import admin
from django.urls import path, include

from main.views import logs_list, registration_view, login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logs/', logs_list, name='logs'),
    path('', include('bots.urls')),
    path('accounts/', include('main.urls')),
    path('register/', registration_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
