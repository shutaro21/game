from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
import json
import base64
import time, datetime
import hmac
import hashlib
import requests
import math

def zoom(request):
    return render(request, 'zoom/index.html', {})

def create_meeting(request):
    # 参考：https://qiita.com/nanbuwks/items/ed74a76a0f294c0bf4ed
    result = {"flg":False}

    API_Key = settings.API_KEY
    API_Secret = settings.API_SECRET
    USER_ID = settings.USER_ID

    if request.GET["password"] != settings.FORM_PASSWORD:
        result["err_str"] = "パスワードが正しくありません。"
        return HttpResponse(json.dumps(result))

    expiration = int(time.time()) + 10 # 有効期間10秒
    header    = base64.urlsafe_b64encode('{"alg":"HS256","typ":"JWT"}'.encode()).replace(b'=', b'') # ヘッダー
    payload   = base64.urlsafe_b64encode(('{"iss":"'+API_Key+'","exp":"'+str(expiration)+'"}').encode()).replace(b'=', b'') # APIキーと>有効期限

    hashdata  = hmac.new(API_Secret.encode(), header+".".encode()+payload, hashlib.sha256) # HMACSHA256でハッシュを作成
    signature = base64.urlsafe_b64encode(hashdata.digest()).replace(b'=', b'') # ハッシュをURL-Save Base64でエンコード
    token = (header+".".encode()+payload+".".encode()+signature).decode()  # トークンをstrで生成

    start_time = timezone.localtime(timezone.now())
    tomorrow = start_time + datetime.timedelta(days=1)
    end_time = datetime.datetime(tomorrow.year,tomorrow.month,tomorrow.day,3,00,00,tzinfo=start_time.tzinfo)

    url = "https://api.zoom.us/v2/"
    headers = {
        'authorization': "Bearer "+token,
        'content-type': "application/json"
        }
    data = {
            "topic": "人狼ボドゲ会",
            "type": "2",
            "start_time": start_time.isoformat()[0:19],
            "timezone": "Asia/Tokyo",
            "duration": math.floor((end_time - start_time).seconds / 60),
            "settings": {
                "join_before_host": True,
                "use_pmi": False,
                'waiting_room': False,
            },
        }
    res = requests.post(url + "users/" + USER_ID + "/meetings", headers=headers, data=json.dumps(data), )
    if res.status_code != 201:
        result["err_str"] = str(res.status_code) + res.text
        return HttpResponse(json.dumps(result))
    context = {
        "topic": res.json()["topic"],
        "start_time": res.json()["start_time"],
        "duration": res.json()["duration"],
        "join_url": res.json()["join_url"],
        "id": res.json()["id"],
        "password": res.json()["password"],
    }
    result["flg"] = True
    result["data"] = json.dumps(context)
    return HttpResponse(json.dumps(result))
