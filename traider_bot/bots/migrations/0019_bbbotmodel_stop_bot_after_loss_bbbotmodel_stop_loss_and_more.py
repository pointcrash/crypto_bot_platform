# Generated by Django 4.2.2 on 2024-06-11 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0018_bbbotmodel_take_after_ml'),
    ]

    operations = [
        migrations.AddField(
            model_name='bbbotmodel',
            name='stop_bot_after_loss',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bbbotmodel',
            name='stop_loss',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bbbotmodel',
            name='stop_loss_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='bbbotmodel',
            name='stop_loss_value_choice',
            field=models.CharField(choices=[('pnl', 'Убытки (PnL)'), ('percent', 'Изменение цены')], default='pnl', max_length=10),
        ),
        migrations.AddField(
            model_name='bbbotmodel',
            name='trailing_in',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bbbotmodel',
            name='trailing_in_percent',
            field=models.CharField(choices=[('0.1', '0.1'), ('0.2', '0.2'), ('0.3', '0.3'), ('0.5', '0.5'), ('1', '1'), ('2', '2'), ('3', '3'), ('5', '5'), ('10', '10')], default='0.5', max_length=5),
        ),
        migrations.AddField(
            model_name='bbbotmodel',
            name='trailing_out',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bbbotmodel',
            name='trailing_out_percent',
            field=models.CharField(choices=[('0.1', '0.1'), ('0.2', '0.2'), ('0.3', '0.3'), ('0.5', '0.5'), ('1', '1'), ('2', '2'), ('3', '3'), ('5', '5'), ('10', '10')], default='0.5', max_length=5),
        ),
        migrations.AlterField(
            model_name='bbbotmodel',
            name='percent_deviation_from_lines',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=5),
        ),
    ]
