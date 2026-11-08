#!/usr/bin/env python3
"""Разовые админ-операции в Telegram-канале через Bot API (запуск из Actions).
Env: TG_OP (метод), TG_MSG_ID, TG_CHAT (канал), TG_FROM (откуда), TG_TO (куда), TG_TEXT.
Для forwardMessage: TG_FROM = источник, TG_TO = получатель.
Печатает полный ответ API — включая реальное описание ошибок."""
import json, os, urllib.request, urllib.parse, urllib.error

TOKEN = os.environ['TELEGRAM_TOKEN']
op = os.environ.get('TG_OP', 'deleteMessage')
msg_id = os.environ.get('TG_MSG_ID', '')
channel = os.environ.get('TG_CHAT', '-1002316192115')
to = os.environ.get('TG_TO', '') or channel
text = os.environ.get('TG_TEXT', '')

params = {}
if op == 'forwardMessage':
    params = {'chat_id': to, 'from_chat_id': channel, 'message_id': msg_id}
elif op == 'getMe':
    params = {}
elif op in ('getChat',):
    params = {'chat_id': channel}
else:
    params = {'chat_id': channel}
    if msg_id: params['message_id'] = msg_id
    if text: params['text'] = text

url = 'https://api.telegram.org/bot%s/%s' % (TOKEN, op)
req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode())
try:
    resp = json.load(urllib.request.urlopen(req, timeout=60))
    out = json.dumps(resp, ensure_ascii=False)
    print('API RESPONSE:', out[:1500])
except urllib.error.HTTPError as e:
    print('HTTP', e.code, 'BODY:', e.read().decode('utf-8', 'replace')[:600])
