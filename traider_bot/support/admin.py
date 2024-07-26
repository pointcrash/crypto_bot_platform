from django.contrib import admin

from support.models import SupportTicket, TicketMessage


@admin.register(SupportTicket)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'stuff', 'status', 'created_at', 'updated_at')
    list_display_links = ('id', 'title',)
    search_fields = ('id', 'title', 'owner', 'stuff', 'status', 'created_at')


@admin.register(TicketMessage)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'ticket', 'is_read', 'created_at')
    list_display_links = ('id', )
    search_fields = ('id', 'author', 'ticket', 'is_read', 'created_at')
