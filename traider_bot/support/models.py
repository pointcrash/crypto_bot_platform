import mimetypes
import os

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class SupportTicket(models.Model):
    TICKET_STATUS_CHOICES = (
        ('NEW', 'NEW'),
        ('TAKEN', 'TAKEN'),
        ('RESOLVED', 'RESOLVED'),
        ('CLOSE', 'CLOSE'),
        ('ARCHIVE', 'ARCHIVE'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_support_tasks')
    stuff = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                              related_name='assigned_support_tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=TICKET_STATUS_CHOICES, default='NEW')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    empty_field = models.BooleanField(default=False)

    def __str__(self):
        return self.title


'''--------------TICKET MESSAGE------------'''


def validate_file(value):
    mime_type, _ = mimetypes.guess_type(value.name)

    if mime_type:
        if not mime_type.startswith('image/') and not mime_type.startswith('video/'):
            raise ValidationError('Файл должен быть изображением или видео.')
    else:
        raise ValidationError('Невозможно определить MIME-тип файла.')


def ticket_file_upload_path(instance, filename):
    # Определяем путь для файла: ticket_files/<ticket_id>/<filename>
    return os.path.join('ticket_files', str(instance.ticket.id), filename)


class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, related_name='messages', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to=ticket_file_upload_path, blank=True, null=True, validators=[validate_file])


'''------------END----------------'''
