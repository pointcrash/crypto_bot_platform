# Generated by Django 4.2.2 on 2024-04-03 08:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveBot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bot_id', models.CharField()),
            ],
        ),
        migrations.CreateModel(
            name='ExchangeService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField()),
            ],
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(unique=True)),
                ('API_TOKEN', models.CharField()),
                ('SECRET_KEY', models.CharField()),
                ('account_type', models.CharField(choices=[('CONTRACT', 'CONTRACT'), ('UNIFIED', 'UNIFIED')], default='CONTRACT', max_length=10, null=True)),
                ('is_mainnet', models.BooleanField()),
                ('url', models.CharField(default='https://api-testnet.bybit.com')),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('service', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.exchangeservice')),
            ],
        ),
    ]
