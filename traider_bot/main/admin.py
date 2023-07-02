from django.contrib import admin

from main.models import Log, Account


# Register your models here.
@admin.register(Log)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'content',)
    list_display_links = ('id', 'content',)


@admin.register(Account)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'is_mainnet')
    list_display_links = ('id', 'name',)
