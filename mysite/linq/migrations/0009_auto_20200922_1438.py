# Generated by Django 3.1.1 on 2020-09-22 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('linq', '0008_auto_20200922_1415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='round',
            name='ng_hit',
            field=models.IntegerField(default=0, null=True, verbose_name='NG的中'),
        ),
        migrations.AlterField(
            model_name='round',
            name='other_hit',
            field=models.IntegerField(default=0, null=True, verbose_name='他ペア的中'),
        ),
    ]
