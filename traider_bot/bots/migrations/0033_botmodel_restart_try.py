# Generated by Django 4.2.2 on 2025-02-04 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0032_botmodel_enabled_manually_botmodel_forcibly_stopped'),
    ]

    operations = [
        migrations.AddField(
            model_name='botmodel',
            name='restart_try',
            field=models.BooleanField(default=False),
        ),
    ]
