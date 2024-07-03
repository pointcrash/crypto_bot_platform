from django.urls import path
from django.contrib.auth import views as auth_views

from main.views import *

urlpatterns = [
    path('', account_list, name='account_list'),
    path('whitelist/', whitelist_view, name='whitelist'),
    path('create/', create_account, name='create_account'),
    path('detail/<int:acc_id>/', edit_account, name='edit_account'),
    path('delete/<int:acc_id>/', delete_account, name='delete_account'),
    path('get_balance/<int:acc_id>/', get_balance, name='get_balance'),
    path('get_account_assets/<int:acc_id>/', get_account_assets_view, name='get_account_assets'),
    path('internal_transfer/<int:acc_id>/', internal_transfer_view, name='internal_transfer'),
    path('withdraw/<int:acc_id>/', withdraw_view, name='withdraw'),
    path('position/recalculate_values', recalculate_values, name='recalculate_values'),
    path('positions_list/', account_position_list, name='account_position_list'),
    path('strategies/', strategies_view, name='strategies'),
    path('all_symbols_update/', update_symbols, name='all_symbols_update'),
    path('restart_all_bots/', restart_all_bots, name='restart_all_bots'),

    path('edit_profile/', edit_profile, name='edit_profile'),

    # path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    #
    # path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    # path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),

]
