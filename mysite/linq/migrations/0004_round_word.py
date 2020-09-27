# Generated by Django 3.1.1 on 2020-09-21 07:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('linq', '0003_remove_player_player_no'),
    ]

    operations = [
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=100, verbose_name='単語')),
            ],
        ),
        migrations.CreateModel(
            name='Round',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_no', models.IntegerField(verbose_name='ラウンド')),
                ('order', models.IntegerField(verbose_name='順番')),
                ('hint1', models.CharField(max_length=100, verbose_name='ヒント1')),
                ('hint2', models.CharField(max_length=100, verbose_name='ヒント2')),
                ('score', models.IntegerField(verbose_name='スコア')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='linq.game')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='linq.player')),
                ('player11', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player11', to='linq.player')),
                ('player12', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player12', to='linq.player')),
                ('player21', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player21', to='linq.player')),
                ('player22', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player22', to='linq.player')),
                ('word', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='linq.word')),
            ],
        ),
    ]