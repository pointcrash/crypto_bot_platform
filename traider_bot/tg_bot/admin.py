from django.contrib import admin

from tg_bot.models import TelegramAccount


@admin.register(TelegramAccount)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'chat_id', 'telegram_username', )
    list_display_links = ('id', 'owner', 'chat_id', 'telegram_username', )
