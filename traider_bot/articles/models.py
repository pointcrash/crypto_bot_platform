from django.db import models
from slugify import slugify

from documentation.models import LANGUAGE_CHOICE


class Article(models.Model):
    ARTICLE_TYPE_CHOICES = (
        ('NEWS', 'NEWS'),
        ('ARTICLE', 'ARTICLE'),
        ('SYMBOL', 'SYMBOL'),
    )

    ARTICLE_CATEGORY_TYPE_CHOICES = (
        ('COMMON', 'COMMON'),
    )

    type = models.CharField(max_length=25, choices=ARTICLE_TYPE_CHOICES)
    category = models.CharField(max_length=25, choices=ARTICLE_CATEGORY_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    slug = models.CharField(max_length=255, unique=True, blank=True)
    cover = models.ImageField(upload_to='news/covers/', blank=True, null=True)
    published = models.BooleanField(default=False)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICE, null=True)
    views = models.IntegerField(default=0)

    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:250]
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug
