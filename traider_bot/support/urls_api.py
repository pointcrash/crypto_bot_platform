from django.urls import path, include
from rest_framework.routers import DefaultRouter

from support.vews_api import TicketViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet)
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('messages/<int:pk>/read/', MessageViewSet.as_view({'post': 'update_read_status'}), name='message-read-status'),
    path('ticket/<int:ticket_id>/messages/', MessageViewSet.as_view({'get': 'list_by_ticket'})),
    path('user-tickets/', TicketViewSet.as_view({'get': 'list_by_user'})),
]
