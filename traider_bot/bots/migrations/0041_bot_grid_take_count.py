# Generated by Django 4.2.2 on 2023-07-09 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0040_alter_bot_deviation_from_lines'),
    ]

    operations = [
        migrations.AddField(
            model_name='bot',
            name='grid_take_count',
            field=models.IntegerField(default=2),
        ),
    ]
