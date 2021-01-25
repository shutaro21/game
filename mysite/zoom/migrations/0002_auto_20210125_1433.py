# Generated by Django 3.1.1 on 2021-01-25 05:33

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zoom', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='flg',
            field=models.IntegerField(choices=[(1, '参加中'), (2, '退室済み')], default=1, verbose_name='参加フラグ'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='participant',
            name='leave_time',
            field=models.DateTimeField(null=True, verbose_name='退室日時'),
        ),
    ]
