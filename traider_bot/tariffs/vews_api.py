from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response

from tariffs.models import UserTariff, Tariff
from tariffs.serializers import UserTariffSerializer, TariffSerializer
from traider_bot.permissions import IsAdminOrReadOnly


class UserTariffViewSet(viewsets.ModelViewSet):
    serializer_class = UserTariffSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = UserTariff.objects.filter(user=self.request.user).order_by('-created_at')
        return queryset

    def list_by_user_id(self, request, user_id):
        user = User.objects.get(id=user_id)
        queryset = UserTariff.objects.filter(user=user).order_by('-created_at')
        if not queryset.exists():
            return Response({"detail": "No tariffs found for this user."}, status=404)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"detail": "No tariffs found for this user."}, status=404)
        queryset = queryset[:1]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TariffReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TariffSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and UserTariff.objects.filter(user=user).first():
            queryset = Tariff.objects.filter(type='ACTIVE').exclude(title='Guest').order_by('price')
        else:
            queryset = Tariff.objects.filter(type='ACTIVE').order_by('price')
        return queryset
