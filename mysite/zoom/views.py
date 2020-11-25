from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import base64
import time, datetime
import hmac
import hashlib
import requests
import math
import logging

ZOOM_API_Key = settings.API_KEY
ZOOM_API_Secret = settings.API_SECRET
ZOOM_USER_ID = settings.USER_ID

logger = logging.getLogger(__name__)
handler = WebhookHandler(settings.CHANNEL_SECRET)
line_bot_api = LineBotApi(settings.CHANNEL_ACCESS_TOKEN)

def zoom(request):
    return render(request, 'zoom/index.html', {})

def create_meeting_api(request):
    result = {"flg":False}

    if request.GET["password"] != settings.FORM_PASSWORD:
        result["err_str"] = "パスワードが正しくありません。"
    else:
        result = create_meeting()

    return HttpResponse(json.dumps(result))

def create_meeting():
    # 参考：https://qiita.com/nanbuwks/items/ed74a76a0f294c0bf4ed
    result = {"flg":False}

    expiration = int(time.time()) + 10 # 有効期間10秒
    header    = base64.urlsafe_b64encode('{"alg":"HS256","typ":"JWT"}'.encode()).replace(b'=', b'') # ヘッダー
    payload   = base64.urlsafe_b64encode(('{"iss":"'+ZOOM_API_Key+'","exp":"'+str(expiration)+'"}').encode()).replace(b'=', b'') # APIキーと>有効期限

    hashdata  = hmac.new(ZOOM_API_Secret.encode(), header+".".encode()+payload, hashlib.sha256) # HMACSHA256でハッシュを作成
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
            "duration": math.ceil((end_time - start_time).seconds / 60),
            "settings": {
                "join_before_host": True,
                "use_pmi": False,
                'waiting_room': False,
            },
        }
    res = requests.post(url + "users/" + ZOOM_USER_ID + "/meetings", headers=headers, data=json.dumps(data), )
    if res.status_code != 201:
        result["err_str"] = str(res.status_code) + res.text
        return HttpResponse(json.dumps(result))
    context = {
        "topic": res.json()["topic"],
        "start_time": timezone.localtime(datetime.datetime.fromisoformat(res.json()["start_time"].replace('Z', '+00:00'))).strftime("%Y/%m/%d %H:%M:%S"),
        "duration": res.json()["duration"],
        "join_url": res.json()["join_url"],
        "id": res.json()["id"],
        "password": res.json()["password"],
    }
    result["flg"] = True
    result["data"] = json.dumps(context)
    return result

@csrf_exempt
def webhook(request):
    logger.debug(request.headers)
    logger.debug(request.body.decode('utf-8'))
    body = request.body.decode('utf-8')
    try:
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        handler.handle(body, signature)
    except InvalidSignatureError:
        HttpResponseForbidden()
    return HttpResponse('OK', status=200)
    
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    if '人狼' in event.message.text:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='人狼なんて\nいるわけないさ'))

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=event.message.text))
