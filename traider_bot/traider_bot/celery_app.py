import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traider_bot.settings')

app = Celery('traider_bot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
