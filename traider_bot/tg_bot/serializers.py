from rest_framework import serializers

from tg_bot.connect_tg_bot import get_chat_id
from tg_bot.models import TelegramAccount


class TelegramAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramAccount
        fields = ['id', 'owner', 'chat_id', 'telegram_username']
        read_only_fields = ['id', 'owner', 'chat_id']

    def create(self, validated_data):
        telegram_username = validated_data.get('telegram_username')
        chat_id = get_chat_id(telegram_username)
        validated_data['chat_id'] = chat_id
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
