from rest_framework import serializers

from documentation.models import DocPage, DocTag


class DocTagSerializer(serializers.ModelSerializer):
    doc_page_title = serializers.ReadOnlyField(source='doc_page.title')

    class Meta:
        model = DocTag
        fields = ['id', 'title', 'doc_page', 'doc_page_title', 'created_at']


class SimpleDocTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocTag
        fields = ['id', 'title']


class DocPageSerializer(serializers.ModelSerializer):
    tags = SimpleDocTagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=DocTag.objects.all(), source='tags'
    )

    class Meta:
        model = DocPage
        fields = ['id', 'title', 'body', 'created_at', 'updated_at', 'tags', 'tag_ids']
