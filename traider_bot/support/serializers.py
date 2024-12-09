from rest_framework import serializers

from support.models import *


class TicketFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketFile
        fields = ['id', 'file', 'uploaded_at']


class MessageSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    files = TicketFileSerializer(many=True, required=False)

    class Meta:
        model = TicketMessage
        fields = ['id', 'ticket', 'author', 'author_username', 'content', 'created_at', 'is_read', 'files']

    def create(self, validated_data):
        files_data = self.initial_data.get('files', [])
        max_files = 5
        if len(files_data) > max_files:
            raise serializers.ValidationError(f"You can upload up to {max_files} files only.")
        message = TicketMessage.objects.create(
            ticket=validated_data['ticket'],
            author=validated_data['author'],
            content=validated_data['content']
        )
        for file in files_data:
            TicketFile.objects.create(
                message=message,
                file=file
            )

        return message


class TicketSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    stuff_username = serializers.ReadOnlyField(source='stuff.username')
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'owner', 'owner_username', 'stuff',
                  'stuff_username', 'messages', 'status']
