from django.contrib import admin

from .models import Bot


@admin.register(Bot)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'symbol', 'side', 'orderType', 'qty', 'price', )
    list_display_links = ('id', 'symbol', )
    search_fields = ('symbol', 'orderType', 'side')
