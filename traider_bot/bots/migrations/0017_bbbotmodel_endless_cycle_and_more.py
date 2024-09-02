# Generated by Django 4.2.2 on 2024-06-03 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0016_bbbotmodel_count_cycles'),
    ]

    operations = [
        migrations.AddField(
            model_name='bbbotmodel',
            name='endless_cycle',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='bbbotmodel',
            name='count_cycles',
            field=models.IntegerField(default=0),
        ),
    ]
