# Generated by Django 4.2.2 on 2023-12-10 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0085_stephedge_move_nipple'),
    ]

    operations = [
        migrations.AddField(
            model_name='bot',
            name='time_create',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='bot',
            name='time_update',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
