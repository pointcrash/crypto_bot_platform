# Generated by Django 4.2.2 on 2024-03-22 19:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0099_alter_bbbotmodel_side'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bbbotmodel',
            name='bot',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bb', to='bots.botmodel'),
        ),
    ]
