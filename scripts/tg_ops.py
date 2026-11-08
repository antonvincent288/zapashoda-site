#!/usr/bin/env python3
"""Разовые админ-операции в Telegram-канале через Bot API (запуск из Actions).
Параметры приходят из env: TG_OP (метод), TG_MSG_ID, TG_CHAT, TG_TEXT.
Печатает полный ответ API — включая реальное описание ошибок."""
import json, os, urllib.request, urllib.parse, urllib.error

TOKEN = os.environ['TELEGRAM_TOKEN']
op = os.environ.get('TG_OP', 'deleteMessage')
msg_id = os.environ.get('TG_MSG_ID', '')
chat = os.environ.get('TG_CHAT', '-1002316192115')
text = os.environ.get('TG_TEXT', '')

params = {'chat_id': chat}
if msg_id: params['message_id'] = msg_id
if text: params['text'] = text

url = 'https://api.telegram.org/bot%s/%s' % (TOKEN, op)
req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode())
try:
    resp = json.load(urllib.request.urlopen(req, timeout=60))
    print('API RESPONSE:', json.dumps(resp, ensure_ascii=False))
except urllib.error.HTTPError as e:
    print('HTTP', e.code, 'BODY:', e.read().decode('utf-8', 'replace')[:600])
