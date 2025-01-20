from django.contrib import admin

from articles.models import Article


@admin.register(Article)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'title', 'slug', 'published', 'language', 'views', 'time_create', 'time_update')
    list_display_links = ('id', 'title', 'slug',)
    search_fields = ('id', 'title', 'slug', 'language', 'published', 'time_create')


