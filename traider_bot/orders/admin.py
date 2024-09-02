from django.contrib import admin

from orders.models import Order, Position


@admin.register(Order)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'bot', 'symbol', 'symbol_name', 'order_id', 'client_order_id', )
    list_display_links = ('id', 'account', 'symbol', )
    search_fields = ('account', 'bot', 'symbol_name', 'order_id')


@admin.register(Position)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'bot', 'symbol', 'symbol_name', 'side', 'qty', )
    list_display_links = ('id', 'account', 'symbol', )
    search_fields = ('account', 'bot', 'symbol_name', 'order_id')
