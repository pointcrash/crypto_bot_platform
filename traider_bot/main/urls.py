from django.urls import path

from main.views import *

urlpatterns = [
    path('', account_list, name='account_list'),
    path('position/recalculate_values', recalculate_values, name='recalculate_values'),
    path('create/', create_account, name='create_account'),
    path('positions_list/', account_position_list, name='account_position_list'),
    path('detail/<int:acc_id>/', edit_account, name='edit_account'),
    path('delete/<int:acc_id>/', delete_account, name='delete_account'),
    path('get_balance/<int:acc_id>/', get_balance, name='get_balance'),
    path('strategies/', strategies_view, name='strategies'),
]
