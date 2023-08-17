from django.urls import path, include

from bots.one_way.views_grid import update_symbols_set
from bots.views import views_bots_type_choice, terminate_bot, delete_bot, reboot_bots

urlpatterns = [
    path('<str:mode>', views_bots_type_choice, name='mode_choice'),
    #
    path('terminate/<int:bot_id>/<int:event_number>/', terminate_bot, name='terminate_bot'),
    path('delete/<int:bot_id>/<int:event_number>/', delete_bot, name='delete_bot'),
    path('update_symbols_set/', update_symbols_set, name='update_symbols_set'),
    path('reboot_bots/', reboot_bots, name='reboot_bots'),
    #
    path('hedge/', include('bots.hedge.urls')),
    path('one_way/', include('bots.one_way.urls')),
]
