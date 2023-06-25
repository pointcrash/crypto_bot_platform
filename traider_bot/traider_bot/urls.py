from django.contrib import admin
from django.urls import path, include

from main.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    # path('orders/', include('orders.urls')),
    path('bots/', include('bots.urls')),

]
