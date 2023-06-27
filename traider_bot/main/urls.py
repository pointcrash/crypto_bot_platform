from django.urls import path

from main.views import *

urlpatterns = [
    path('', account_list, name='account_list'),
    path('create/', create_account, name='create_account'),
    path('detail/<int:acc_id>/', edit_account, name='edit_account'),
    path('/delete/<int:acc_id>/', delete_account, name='delete_account'),

]
