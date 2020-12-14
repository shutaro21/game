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
import re

ZOOM_API_Key = settings.API_KEY
ZOOM_API_Secret = settings.API_SECRET
ZOOM_USER_ID = settings.USER_ID
APPROVED_USERS = settings.APPROVED_USERS
APPROVED_GROUPS = settings.APPROVED_GROUPS
APPROVED_ROOMS = settings.APPROVED_ROOMS

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

def get_zoom_token():
    expiration = int(time.time()) + 10 # 有効期間10秒
    header    = base64.urlsafe_b64encode('{"alg":"HS256","typ":"JWT"}'.encode()).replace(b'=', b'') # ヘッダー
    payload   = base64.urlsafe_b64encode(('{"iss":"'+ZOOM_API_Key+'","exp":"'+str(expiration)+'"}').encode()).replace(b'=', b'') # APIキーと>有効期限

    hashdata  = hmac.new(ZOOM_API_Secret.encode(), header+".".encode()+payload, hashlib.sha256) # HMACSHA256でハッシュを作成
    signature = base64.urlsafe_b64encode(hashdata.digest()).replace(b'=', b'') # ハッシュをURL-Save Base64でエンコード
    token = (header+".".encode()+payload+".".encode()+signature).decode()  # トークンをstrで生成
    return token

def create_meeting(topic=None, fd=None, fh=None, th=None, agenda=None):
    # 参考：https://qiita.com/nanbuwks/items/ed74a76a0f294c0bf4ed
    result = {"flg":False}
    token = get_zoom_token()

    current_time = timezone.localtime(timezone.now())
    start_y = current_time.year
    start_m = current_time.month
    start_d = current_time.day
    start_h = current_time.hour
    start_mi = current_time.minute
    if fh:
        start_h = fh
        start_mi = 0
        if fd:
            start_d = fd
            if fd < current_time.day:
                if current_time.month == 12:
                    start_y = current_time.year + 1
                    start_m = 1
                else:
                    start_m = current_time.month + 1
    start_time = datetime.datetime(start_y,start_m,start_d,start_h,start_mi,00,tzinfo=current_time.tzinfo)
    tomorrow = start_time + datetime.timedelta(days=1)
    end_h = th if th else 3
    if end_h < start_h:
        end_time = datetime.datetime(tomorrow.year,tomorrow.month,tomorrow.day,end_h,00,00,tzinfo=current_time.tzinfo)
    else:
        end_time = datetime.datetime(start_time.year,start_time.month,start_time.day,end_h,00,00,tzinfo=current_time.tzinfo)

    res = get_meetings()
    if not res["flg"]:
        result["err_str"] = res["err_str"]
        return result
    existing_meetings = res["data"]
    if existing_meetings:
        for meeting in existing_meetings:
            e_start_time = datetime.datetime.fromisoformat(meeting["start_time"].replace('Z', '+00:00'))
            e_end_time = e_start_time + datetime.timedelta(minutes=meeting["duration"])
            if (start_time < e_end_time and end_time > e_start_time):
                result["err_str"] = '時間が重複した会議があるよ！'
                return result

    url = "https://api.zoom.us/v2/"
    headers = {
        'authorization': "Bearer "+token,
        'content-type': "application/json"
        }
    data = {
            "topic": topic if topic else "人狼ボドゲ会",
            "agenda": agenda if agenda else "-",
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
    start_time = datetime.datetime.fromisoformat(res.json()["start_time"].replace('Z', '+00:00'))
    end_time = start_time + datetime.timedelta(minutes=data["duration"])
    context = {
        "topic": res.json()["topic"],
        "start_time": timezone.localtime(start_time).strftime("%Y/%m/%d %H:%M:%S"),
        "end_time": timezone.localtime(end_time).strftime("%Y/%m/%d %H:%M:%S"),
        "join_url": res.json()["join_url"],
        "id": res.json()["id"],
        "password": res.json()["password"],
    }
    result["flg"] = True
    result["data"] = json.dumps(context)
    return result

def delete_meetings(source_id=None):
    result = {"flg":False}
    token = get_zoom_token()
    url = "https://api.zoom.us/v2/"
    headers = {
        'authorization': "Bearer "+token,
        'content-type': "application/json"
        }
    res = get_meetings()
    if not res["flg"]:
        result["err_str"] = res["err_str"]
        return result
    meetings = res["data"]
    if not meetings:
        result["flg"] = True
        result["msg"] = "削除する会議は無かったよ！"
        return result
    cnt_del = 0
    for meeting in meetings:
        res = requests.get(url + 'meetings/' + str(meeting["id"]), headers=headers, )
        if res.status_code != 200:
            result["err_str"] = '会議情報の取得に失敗したよ！\n' + str(res.status_code) + res.text
            return result
        if not (source_id and res.json().get("agenda")!=source_id):
            res = requests.delete(url + 'meetings/' + str(meeting["id"]), headers=headers, )
            if res.status_code != 204:
                result["err_str"] = '削除に失敗したよ！\n' + str(res.status_code) + res.text
                return result
            cnt_del += 1
    if cnt_del == 0:
        result["flg"] = True
        result["msg"] = "削除する会議は無かったよ！"
        return result
    result["flg"] = True
    result["msg"] = str(cnt_del) + "件の会議を削除したよ！"
    return result

def get_meetings():
    result = {"flg":False}
    token = get_zoom_token()
    url = "https://api.zoom.us/v2/"
    headers = {
        'authorization': "Bearer "+token,
        'content-type': "application/json"
        }
    params = {
            "type": "upcoming",
        }
    res = requests.get(url + "users/" + ZOOM_USER_ID + "/meetings", headers=headers, params=params, )
    if res.status_code != 200:
        result["err_str"] = '一覧取得に失敗したよ！。\n' + str(res.status_code) + res.text
        return result
    meetings = res.json().get("meetings")
    result["flg"] = True
    result["data"] = meetings
    return result

def post_chaplus(message):
    result = {"flg":False}
    url = "https://www.chaplus.jp/v1/chat"
    headers = {
        'content-type': "application/json"
        }
    params = {
            "apikey": settings.CHAPLUS_API_KEY,
        }
    data = {
            "utterance": message,
            "username": "あなた",
            "agentState": {
                "agentName": "モブ爺",
                "tone": "normal",
                "age": "80",
            },
        }
    res = requests.post(url, headers=headers, params=params, data=json.dumps(data), )
    if res.status_code != 200:
        result["err_str"] = '会話取得に失敗しました。\n' + str(res.status_code) + res.text
        return result
    logger.debug(res.json())
    response = res.json().get("bestResponse").get("utterance")
    result["flg"] = True
    result["response"] = response
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
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='ハッハッハ！\nただのウワサ話だよ。\n人狼なんているわけないさ！'))
    if (event.source.user_id in APPROVED_USERS or
        event.source.type == "group" and event.source.group_id in APPROVED_GROUPS or
        event.source.type == "room" and event.source.room_id in APPROVED_ROOMS):
        if event.source.type == "group":
            source_id = event.source.group_id
        elif event.source.type == "room":
            source_id = event.source.room_id
        else:
            source_id = event.source.user_id
        if 'モブ' in event.message.text:
            if '会議' in event.message.text and '作' in event.message.text:
                topic = re.search(r'「(.+)」',event.message.text).group(1) if re.search(r'「(.+)」',event.message.text) else None
                fd, fh, td, th = None, None, None, None
                re_from_d = re.search(r'(\d+)日(\d+)時から',event.message.text)
                re_from_h = re.search(r'(\d+)時から',event.message.text)
                re_to_h = re.search(r'(\d+)時まで',event.message.text)
                if re_from_d:
                    fd = int(re_from_d.groups()[0])
                    fh = int(re_from_d.groups()[1])
                elif re_from_h:
                    fh = int(re_from_h.groups()[0])
                if re_to_h:
                    th = int(re_to_h.groups()[0])
                result = create_meeting(topic, fd, fh, th, source_id)
                if result["flg"]:
                    data = json.loads(result["data"])
                    response_message = "会議を作成したよ！\n" \
                                "会議タイトル：" + data["topic"] + "\n" \
                                "開始時刻：" + data["start_time"] + "\n" \
                                "終了時刻：" + data["end_time"] + "\n" \
                                "参加URL：" + data["join_url"] + "\n" \
                                "会議ID：" + str(data["id"]) + "\n" \
                                "会議パスワード：" + str(data["password"])
                else:
                    response_message = result["err_str"]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
            if '会議' in event.message.text and ('削' in event.message.text or '消' in event.message.text):
                result = delete_meetings() if '全部' in event.message.text else delete_meetings(source_id)
                if result["flg"]:
                    response_message = result["msg"]
                else:
                    response_message = result["err_str"]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
            if '会議' in event.message.text and ('教えて' in event.message.text or '一覧' in event.message.text or '予定' in event.message.text):
                result = get_meetings()
                if result["flg"]:
                    data = result["data"]
                    if result["data"]:
                        response_message = "予定されている会議一覧だよ！"
                        for meeting in data:
                            start_time = datetime.datetime.fromisoformat(meeting["start_time"].replace('Z', '+00:00'))
                            end_time = start_time + datetime.timedelta(minutes=meeting["duration"])
                            response_message = response_message + "\n" + meeting["topic"] + "：" \
                                + timezone.localtime(start_time).strftime("%Y/%m/%d %H:%M:%S") + "～" \
                                + timezone.localtime(end_time).strftime("%Y/%m/%d %H:%M:%S")
                    else:
                        response_message = "予定されている会議は無いよ！"
                else:
                    response_message = result["err_str"]
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
        conv = re.search(r'モブ.*、(.+)',event.message.text)
        if conv:
            result = post_chaplus(conv.group(1))
            if result["flg"]:
                response_message = result["response"]
            else:
                response_message = result["err_str"]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))
            
