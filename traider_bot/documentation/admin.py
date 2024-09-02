from django.contrib import admin

from documentation.models import DocPage, DocTag, DocCategory


@admin.register(DocPage)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'body', 'created_at', 'updated_at')
    list_display_links = ('id', 'title',)
    search_fields = ('id', 'title', 'created_at')


@admin.register(DocTag)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'get_doc_pages', 'created_at')
    list_display_links = ('id', 'title')
    search_fields = ('id', 'title', 'get_doc_pages', 'created_at')

    def get_doc_pages(self, obj):
        return ", ".join([str(d.id) for d in obj.doc_page.all()])
    get_doc_pages.short_description = 'doc_pages'


@admin.register(DocCategory)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'get_doc_pages')
    list_display_links = ('id', 'title',)
    search_fields = ('id', 'title', 'get_doc_pages')

    def get_doc_pages(self, obj):
        return ", ".join([str(d.id) for d in obj.doc_page.all()])
    get_doc_pages.short_description = 'doc_pages'
