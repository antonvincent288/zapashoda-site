#!/usr/bin/env python3
"""Разовые админ-операции в Telegram-канале через Bot API (запуск из Actions).
Env: TG_OP (метод), TG_MSG_ID, TG_CHAT (канал), TG_FROM/TG_TO, TG_TEXT, TG_FILE.
Для forwardMessage: TG_FROM = источник, TG_TO = получатель.
Для sendVideoFile: TG_FILE = путь в репо, TG_TEXT = подпись.
Печатает полный ответ API — включая реальное описание ошибок."""
import json, os, urllib.request, urllib.parse, urllib.error, uuid

TOKEN = os.environ['TELEGRAM_TOKEN']
op = os.environ.get('TG_OP', 'deleteMessage')
msg_id = os.environ.get('TG_MSG_ID', '')
channel = os.environ.get('TG_CHAT', '-1002316192115')
to = os.environ.get('TG_TO', '') or channel
text = os.environ.get('TG_TEXT', '')
tgfile = os.environ.get('TG_FILE', '')

def post_simple(method, params):
    url = 'https://api.telegram.org/bot%s/%s' % (TOKEN, method)
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode())
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=60))
        print('API RESPONSE:', json.dumps(resp, ensure_ascii=False)[:1500])
    except urllib.error.HTTPError as e:
        print('HTTP', e.code, 'BODY:', e.read().decode('utf-8', 'replace')[:600])

if op == 'sendVideoFile':
    boundary = uuid.uuid4().hex
    parts = []
    parts.append(('--%s\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n%s\r\n' % (boundary, channel)).encode())
    if text:
        parts.append(('--%s\r\nContent-Disposition: form-data; name="caption"\r\n\r\n%s\r\n' % (boundary, text)).encode())
    parts.append(('--%s\r\nContent-Disposition: form-data; name="supports_streaming"\r\n\r\ntrue\r\n' % boundary).encode())
    parts.append(('--%s\r\nContent-Disposition: form-data; name="video"; filename="%s"\r\nContent-Type: video/mp4\r\n\r\n' % (boundary, os.path.basename(tgfile))).encode())
    parts.append(open(tgfile, 'rb').read())
    parts.append(('\r\n--%s--\r\n' % boundary).encode())
    url = 'https://api.telegram.org/bot%s/sendVideo' % TOKEN
    req = urllib.request.Request(url, data=b''.join(parts),
        headers={'Content-Type': 'multipart/form-data; boundary=%s' % boundary})
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=180))
        print('API RESPONSE:', json.dumps(resp, ensure_ascii=False)[:1500])
    except urllib.error.HTTPError as e:
        print('HTTP', e.code, 'BODY:', e.read().decode('utf-8', 'replace')[:600])
elif op == 'setChatMenuButton':
    post_simple('setChatMenuButton', {'menu_button': text})
elif op == 'getChatMenuButton':
    post_simple('getChatMenuButton', {})
elif op == 'getMe':
    post_simple('getMe', {})
elif op == 'getChat':
    post_simple('getChat', {'chat_id': channel})
elif op == 'forwardMessage':
    post_simple('forwardMessage', {'chat_id': to, 'from_chat_id': channel, 'message_id': msg_id})
else:
    params = {'chat_id': channel}
    if msg_id: params['message_id'] = msg_id
    if text: params['text'] = text
    post_simple(op, params)
