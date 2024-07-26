from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import *
from .serializers import MessageSerializer, TicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = TicketMessage.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update_read_status(self, request, pk=None):
        try:
            message = self.get_object()
            message.is_read = request.data.get('is_read', True)
            message.save()
            return Response({'status': 'read status updated'})
        except TicketMessage.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
