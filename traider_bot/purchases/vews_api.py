from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import ServiceProduct, Purchase
from .serializers import ServiceProductSerializer, PurchaseSerializer


class ServiceProductViewSet(viewsets.ModelViewSet):
    queryset = ServiceProduct.objects.all()
    serializer_class = ServiceProductSerializer

    permission_classes = [IsAdminUser]


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Purchase.objects.all()
        return Purchase.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
