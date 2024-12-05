from django.db import models

LANGUAGE_CHOICE = (
    ('en', 'en'),
    ('ru', 'ru'),
)


class DocPage(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICE, default='en')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class DocTag(models.Model):
    title = models.CharField(max_length=50, unique=True)
    doc_page = models.ManyToManyField(DocPage, related_name='tags', blank=True)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICE, default='en')
    created_at = models.DateTimeField(auto_now_add=True)


class DocCategory(models.Model):
    title = models.CharField(max_length=200)
    doc_page = models.ManyToManyField(DocPage, related_name='category')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICE, default='en')
