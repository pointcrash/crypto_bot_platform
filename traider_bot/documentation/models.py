from django.db import models


class DocPage(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class DocTag(models.Model):
    title = models.CharField(max_length=50, unique=True)
    doc_page = models.ManyToManyField(DocPage, related_name='tags', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DocCategory(models.Model):
    title = models.CharField(max_length=200)
    doc_page = models.ManyToManyField(DocPage, related_name='category')
