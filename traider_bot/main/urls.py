from django.urls import path

from bots.views import get_balance_views
from main.views import *

urlpatterns = [
    path('', account_list, name='account_list'),
    path('create/', create_account, name='create_account'),
    path('detail/<int:acc_id>/', edit_account, name='edit_account'),
    path('delete/<int:acc_id>/', delete_account, name='delete_account'),
    path('balance/<int:acc_id>/', get_balance_views, name='balance'),
]
