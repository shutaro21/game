from django.db import models

class Participant(models.Model):
    meeting_id = models.CharField('会議ID', max_length=64)
    user_id = models.CharField('ユーザID', max_length=64)
    user_name = models.CharField('ユーザ名', max_length=128)
    flg = models.IntegerField('参加フラグ', choices=((1,'参加中'),(2,'退室済み'),))
    join_time = models.DateTimeField('参加日時', auto_now_add=True)
    leave_time = models.DateTimeField('退室日時', null=True)

