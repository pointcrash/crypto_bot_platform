from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from articles.models import Article
from articles.serializers import ArticleSerializer


class ArticleReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = super().get_queryset()
        language = self.request.query_params.get('language')
        queryset = queryset.filter(language=language) if language else queryset
        queryset = queryset.filter(published=True)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        article = self.get_object()

        article.views += 1
        article.save(update_fields=["views"])

        serializer = self.get_serializer(article)
        return Response(serializer.data)


class ArticleForAdminViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = super().get_queryset()
        language = self.request.query_params.get('language')
        queryset = queryset.filter(language=language) if language else queryset
        return queryset

