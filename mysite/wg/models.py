from django.db import models

class Template(models.Model):
    name = models.CharField('名称', max_length=64)
    cons = models.TextField('構成')
    del_flg = models.BooleanField('削除フラグ', default=False)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('変更日時', auto_now=True)
