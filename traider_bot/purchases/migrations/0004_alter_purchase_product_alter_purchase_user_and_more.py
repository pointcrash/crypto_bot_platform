# Generated by Django 4.2.2 on 2024-10-27 19:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tariffs', '0006_alter_tariff_type'),
        ('purchases', '0003_purchase_order_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchase',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='purchases.serviceproduct'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='serviceproduct',
            name='tariff',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tariffs.tariff'),
        ),
    ]
