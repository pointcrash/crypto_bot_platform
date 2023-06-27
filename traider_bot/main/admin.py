from django.contrib import admin

from main.models import Log, Account


# Register your models here.
@admin.register(Log)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'content',)


@admin.register(Account)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_mainnet')
