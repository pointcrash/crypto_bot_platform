# Generated by Django 4.2.2 on 2024-10-24 16:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_alter_accounthistory_cash_flow_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountbalance',
            name='asset',
            field=models.CharField(default='USDT', max_length=25),
        ),
        migrations.AlterField(
            model_name='accountbalance',
            name='available_balance',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='accountbalance',
            name='balance',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='accountbalance',
            name='un_pnl',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
    ]
