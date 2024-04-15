# Generated by Django 4.2.2 on 2024-01-23 15:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_exchangeservice_account_service'),
        ('bots', '0090_exchangeservice_bot_service'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bot',
            name='service',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.exchangeservice'),
        ),
        migrations.DeleteModel(
            name='ExchangeService',
        ),
    ]
