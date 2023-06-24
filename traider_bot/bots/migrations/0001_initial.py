# Generated by Django 4.2.2 on 2023-06-24 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('linear', 'Linear')], default='linear', max_length=10)),
                ('symbol', models.CharField(max_length=100)),
                ('isLeverage', models.IntegerField(default=10)),
                ('side', models.CharField(choices=[('Buy', 'Buy'), ('Sell', 'Sell')], default='Buy', max_length=4)),
                ('orderType', models.CharField(choices=[('Limit', 'Limit'), ('Market', 'Market')], default='Limit', max_length=10)),
                ('qty', models.DecimalField(decimal_places=3, max_digits=10)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
            ],
        ),
    ]
