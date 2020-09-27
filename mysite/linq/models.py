from django.db import models

class Game(models.Model):
    player_cnt = models.IntegerField('プレイヤー人数')
    start_score = models.IntegerField('開始スコア')
    end_score = models.IntegerField('終了スコア')

class Player(models.Model):
    game = models.ForeignKey('Game', on_delete=models.CASCADE)
    name = models.CharField('プレイヤー名', max_length=50)
    score = models.IntegerField('スコア')

class Word(models.Model):
    word = models.CharField('単語', max_length=100)

class Round(models.Model):
    game = models.ForeignKey('Game', on_delete=models.CASCADE)
    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    round_no = models.IntegerField('ラウンド')
    order = models.IntegerField('順番')
    word = models.CharField('Word', max_length=100)
    hint1 = models.CharField('ヒント1', max_length=100, null=True)
    hint2 = models.CharField('ヒント2', max_length=100, null=True)
    poll11 = models.ForeignKey('self', related_name='poll11_p', on_delete=models.CASCADE, null=True)
    poll12 = models.ForeignKey('self', related_name='poll12_p', on_delete=models.CASCADE, null=True)
    poll21 = models.ForeignKey('self', related_name='poll21_p', on_delete=models.CASCADE, null=True)
    poll22 = models.ForeignKey('self', related_name='poll22_p', on_delete=models.CASCADE, null=True)
    poll1_result = models.IntegerField('投票１結果', null=True)
    poll2_result = models.IntegerField('投票２結果', null=True)
    score = models.IntegerField('スコア', null=True)
    pair_player = models.ForeignKey('self', related_name='pair_player_p', on_delete=models.CASCADE, null=True)
    self_hit = models.BooleanField('自ペア的中', null=True)
    other_hit = models.IntegerField('他ペア的中', null=True, default=0)
    ng_hit = models.IntegerField('NG的中', null=True, default=0)
    be_other_hit = models.IntegerField('被他ペア的中', null=True, default=0)
    be_ng_hit = models.IntegerField('被NG的中', null=True, default=0)