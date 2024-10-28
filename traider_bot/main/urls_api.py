from django.urls import path, include
from rest_framework.routers import DefaultRouter

from main.views_api import *

router = DefaultRouter()
router.register(r'account-balance-history', AccountBalanceHistoryView, basename='account-balance-history')
router.register(r'account-transaction-history', AccountTransactionHistoryView, basename='account-transaction-history')


urlpatterns = [
    path('', include(router.urls)),

    path('user/', CurrentUserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('users/', UsersViewSet.as_view({'get': 'list'})),
    path('users/<int:pk>/', UsersViewSet.as_view({'put': 'update', 'get': 'retrieve', 'delete': 'destroy'})),

    path('accounts/', AccountsViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('accounts/<int:pk>/', AccountsViewSet.as_view({'put': 'update', 'get': 'retrieve', 'delete': 'destroy', 'patch': 'partial_update'})),
    path('accounts/<int:acc_id>/get-futures-balance/', GetFuturesBalanceView.as_view()),
    path('accounts/all/get-futures-balances/', GetFuturesBalanceAllAccountsView.as_view()),
    path('accounts/<int:acc_id>/get-fund-balance/', GetFundBalanceView.as_view()),
    path('accounts/<int:acc_id>/internal-transfer/', InternalTransferView.as_view()),
    path('accounts/by-owner/<int:owner_id>/', AccountsViewSet.as_view({'get': 'list_by_owner'})),

    path('exchange-services/', ExchangeServiceReadOnlyViewSet.as_view({'get': 'list'})),
    path('get-trusted-ip/', GetTrustedIPView.as_view(), name='get_trusted_ip'),
    path('referrals/<str:referral_code>/add/', AddReferredUserView.as_view(), name='add-referred-user'),

    path('update_symbols', UpdateSymbolsView.as_view(), name='update_symbols'),
    path('accounts/connect_ws/', AccountWSConnectView.as_view(), name='account_ws_connect'),

]
