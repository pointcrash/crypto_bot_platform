from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from documentation.models import DocPage, DocTag
from documentation.serializers import DocPageSerializer, DocTagSerializer


class DocPageReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocPage.objects.all()
    serializer_class = DocPageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        language = self.request.query_params.get('language')
        queryset = queryset.filter(language=language) if language else queryset
        return queryset


class DocPageForAdminViewSet(viewsets.ModelViewSet):
    queryset = DocPage.objects.all()
    serializer_class = DocPageSerializer
    permission_classes = [IsAdminUser]


class DocTagViewSet(viewsets.ModelViewSet):
    queryset = DocTag.objects.all()
    serializer_class = DocTagSerializer
    permission_classes = [IsAdminUser]

