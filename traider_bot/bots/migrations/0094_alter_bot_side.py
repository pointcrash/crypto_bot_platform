# Generated by Django 4.2.2 on 2024-03-20 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0093_alter_bot_interval_alter_bot_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bot',
            name='side',
            field=models.CharField(choices=[('Buy', 'Buy'), ('Sell', 'Sell'), ('FB', 'First Band')], default='Auto', max_length=4),
        ),
    ]
