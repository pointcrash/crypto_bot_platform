from django.contrib import admin

from bots.models import Log
from main.models import Account, ActiveBot


# Register your models here.


@admin.register(Account)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'is_mainnet')
    list_display_links = ('id', 'name',)
    search_fields = ('id', 'name', 'owner', 'is_mainnet')


@admin.register(ActiveBot)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'bot_id')
    list_display_links = ('id', 'bot_id',)
    search_fields = ('id', 'bot_id',)
