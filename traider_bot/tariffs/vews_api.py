from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from tariffs.models import UserTariff, Tariff
from tariffs.serializers import UserTariffSerializer, TariffSerializer


class UserTariffViewSet(viewsets.ModelViewSet):
    serializer_class = UserTariffSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            queryset = UserTariff.objects.all()
        else:
            queryset = UserTariff.objects.filter(user=user)
        return queryset

    def list_by_user_id(self, request, user_id):
        user = User.objects.get(id=user_id)
        queryset = UserTariff.objects.filter(user=user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"detail": "No tariffs found for this user."}, status=404)


class TariffReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer
    permission_classes = [IsAuthenticated]
