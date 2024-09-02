# Generated by Django 4.2.2 on 2024-07-12 11:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0023_userbotlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='Grid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('low_price', models.DecimalField(decimal_places=7, max_digits=20)),
                ('high_price', models.DecimalField(decimal_places=7, max_digits=20)),
                ('grid_count', models.IntegerField()),
                ('bot', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='bots.botmodel')),
            ],
        ),
    ]
