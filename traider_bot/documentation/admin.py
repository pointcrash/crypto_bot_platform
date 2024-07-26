from django.contrib import admin

from documentation.models import DocPage, DocTag


@admin.register(DocPage)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'body', 'created_at', 'updated_at')
    list_display_links = ('id', 'title',)
    search_fields = ('id', 'title', 'created_at')


@admin.register(DocTag)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'doc_page', 'created_at')
    list_display_links = ('id', 'title')
    search_fields = ('id', 'title', 'doc_page', 'created_at')
