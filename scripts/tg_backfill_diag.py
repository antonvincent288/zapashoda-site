#!/usr/bin/env python3
"""Диагностика: те же правки, но печатаем description ошибки Telegram."""
import json, os, urllib.request, urllib.parse

TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL = os.environ['CHANNEL_ID']
entries = json.load(open('scripts/backfill_map.json', encoding='utf-8'))
e = entries[0]
data = {'chat_id': CHANNEL, 'message_id': e['msg_id'], 'text': e['html'], 'parse_mode': 'HTML'}
req = urllib.request.Request('https://api.telegram.org/bot%s/editMessageText' % TOKEN,
    data=urllib.parse.urlencode(data).encode(), headers={'User-Agent': 'zapashoda-bot'})
try:
    r = json.load(urllib.request.urlopen(req, timeout=60))
    print('ok:', r.get('ok'), r.get('description'))
except urllib.error.HTTPError as ex:
    print('HTTP', ex.code, ex.read().decode()[:300])
