from django.urls import path

from main.views_api import UsersViewSet, AccountsViewSet, CurrentUserViewSet

urlpatterns = [
    path('user/', CurrentUserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('users/', UsersViewSet.as_view({'get': 'list'})),
    path('users/<int:pk>/', UsersViewSet.as_view({'put': 'update', 'get': 'retrieve', 'delete': 'destroy'})),

    path('accounts/', AccountsViewSet.as_view({'get': 'list'})),
    path('accounts/<int:pk>/', AccountsViewSet.as_view({'put': 'update', 'get': 'retrieve', 'delete': 'destroy'})),
    # path('accounts/owner/<int:owner_id>/', AccountsViewSet.as_view({'get': 'list_by_owner'})),

]
