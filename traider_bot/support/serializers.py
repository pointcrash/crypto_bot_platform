from rest_framework import serializers

from support.models import *


class MessageSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = TaskMessage
        fields = ['id', 'task', 'author', 'author_username', 'content', 'created_at', 'is_read']


class TaskSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    stuff_username = serializers.ReadOnlyField(source='stuff.username')
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTask
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'owner', 'owner_username', 'stuff',
                  'stuff_username', 'messages', 'status']
