# Generated by Django 3.1.1 on 2020-11-17 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wg', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='del_flg',
            field=models.BooleanField(default=False, verbose_name='削除フラグ'),
        ),
    ]
