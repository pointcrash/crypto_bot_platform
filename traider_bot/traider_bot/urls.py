from django.contrib import admin
from django.urls import path, include

from main.views import home, logs_list

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    # path('profile/', profile_view, name='profile'),
    path('logs/', logs_list, name='logs'),
    # path('orders/', include('orders.urls')),
    path('bots/', include('bots.urls')),

]
