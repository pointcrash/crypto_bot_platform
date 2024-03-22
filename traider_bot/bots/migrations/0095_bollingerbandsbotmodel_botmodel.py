# Generated by Django 4.2.2 on 2024-03-22 15:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_alter_account_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bots', '0094_alter_bot_side'),
    ]

    operations = [
        migrations.CreateModel(
            name='BollingerBandsBotModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('side', models.CharField(choices=[('Buy', 'Buy'), ('Sell', 'Sell'), ('FB', 'First Band')], default='Auto', max_length=4)),
                ('orderType', models.CharField(blank=True, choices=[('Limit', 'Limit'), ('Market', 'Market')], default='Limit', max_length=10)),
                ('qty_kline', models.IntegerField(default=20)),
                ('interval', models.CharField(choices=[('1', '1'), ('3', '3'), ('5', '5'), ('15', '15'), ('30', '30'), ('60', '60'), ('120', '120'), ('240', '240'), ('360', '360'), ('720', '720'), ('D', 'D'), ('W', 'W'), ('M', 'M')], default='15', max_length=3)),
                ('d', models.IntegerField(default=2)),
                ('take_on_ml', models.BooleanField(default=True)),
                ('take_on_ml_percent', models.DecimalField(decimal_places=2, default=50, max_digits=5)),
                ('auto_avg', models.BooleanField(default=False)),
                ('avg_percent', models.DecimalField(decimal_places=2, default=100, max_digits=5)),
                ('is_deviation_from_lines', models.BooleanField(default=False)),
                ('percent_deviation_from_lines', models.DecimalField(decimal_places=5, default=0, max_digits=10)),
                ('dfm', models.DecimalField(decimal_places=3, default=30, max_digits=5)),
                ('chw', models.DecimalField(decimal_places=3, default=2, max_digits=5)),
                ('dfep', models.DecimalField(blank=True, decimal_places=3, max_digits=5, null=True)),
                ('max_margin', models.IntegerField(blank=True, null=True)),
                ('time_create', models.DateTimeField(auto_now_add=True, null=True)),
                ('time_update', models.DateTimeField(auto_now=True, null=True)),
                ('bot', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bots.bot')),
            ],
        ),
        migrations.CreateModel(
            name='BotModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(blank=True, default='linear', max_length=10)),
                ('leverage', models.IntegerField(default=10)),
                ('amount_long', models.IntegerField()),
                ('amount_short', models.IntegerField(blank=True, null=True)),
                ('margin_type', models.CharField(choices=[('CROSS', 'CROSS'), ('ISOLATED', 'ISOLATED')], default='CROSS', max_length=10)),
                ('work_model', models.CharField(max_length=10)),
                ('pnl', models.DecimalField(blank=True, decimal_places=5, default=0, max_digits=20, null=True)),
                ('is_active', models.BooleanField(default=False)),
                ('time_create', models.DateTimeField(auto_now_add=True, null=True)),
                ('time_update', models.DateTimeField(auto_now=True, null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='main.account')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('symbol', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bots.symbol')),
            ],
            options={
                'unique_together': {('account', 'symbol')},
            },
        ),
    ]
