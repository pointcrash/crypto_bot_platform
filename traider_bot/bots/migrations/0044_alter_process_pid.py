# Generated by Django 4.2.2 on 2023-07-11 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0043_process'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process',
            name='pid',
            field=models.CharField(blank=True, default=None, null=True),
        ),
    ]
