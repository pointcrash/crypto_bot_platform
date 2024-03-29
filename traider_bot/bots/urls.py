from django.urls import path, include

from bots.SimpleHedge.views import averaging_simple_hedge_view
from bots.StepHedge.views import on_off_move_nipple
from bots.SetZeroPsn.views import start_set_zero_psn_bot, stop_set_zero_psn_bot
from bots.views import views_bots_type_choice, delete_bot, stop_bot, bot_list, bot_start

urlpatterns = [
    path('list/', bot_list, name='bot_list'),
    path('start/<int:bot_id>', bot_start, name='bot_start'),
    #
    path('<str:mode>', views_bots_type_choice, name='mode_choice'),
    #
    path('terminate/<int:bot_id>/<int:event_number>/', stop_bot, name='terminate_bot'),
    path('delete/<int:bot_id>/<int:event_number>/', delete_bot, name='delete_bot'),
    #
    path('bb/', include('bots.bb.urls')),
    path('start_set_zero_psn_bot/<int:acc_id>/<str:symbol_name>/<int:trend>', start_set_zero_psn_bot, name='start_set_zero_psn_bot'),
    path('stop_set_zero_psn_bot/<int:acc_id>/<str:symbol_name>/', stop_set_zero_psn_bot, name='stop_set_zero_psn_bot'),
    #
    path('averaging_simple_hedge/<int:bot_id>/', averaging_simple_hedge_view, name='averaging_simple_hedge'),
    #
    path('on_off_move_nipple/<int:bot_id>/', on_off_move_nipple, name='on_off_move_nipple'),

]
