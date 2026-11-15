#!/usr/bin/env python3
"""Бэкфилл хэштегов старых постов: editMessageText по маппингу backfill_map.json.
Редактирует только сообщения бота — безопасно при неверном msg_id (Telegram вернёт ошибку)."""
import json, os, sys, urllib.request, urllib.parse

TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL = os.environ['CHANNEL_ID']
MAP_PATH = 'scripts/backfill_map.json'
DONE_PATH = 'scripts/backfill_done.json'
done = []
if os.path.exists(DONE_PATH):
    done = json.load(open(DONE_PATH, encoding='utf-8'))

entries = json.load(open(MAP_PATH, encoding='utf-8'))
ok, fail, skip = 0, 0, 0
for e in entries:
    if e['msg_id'] in done:
        skip += 1
        continue
    data = {'chat_id': CHANNEL, 'message_id': e['msg_id'], 'text': e['html'], 'parse_mode': 'HTML'}
    if e.get('buttons'):
        data['reply_markup'] = json.dumps({'inline_keyboard': e['buttons']}, ensure_ascii=False)
    req = urllib.request.Request('https://api.telegram.org/bot%s/editMessageText' % TOKEN,
        data=urllib.parse.urlencode(data).encode(), headers={'User-Agent': 'zapashoda-bot'})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=60))
        if r.get('ok'):
            ok += 1
            done.append(e['msg_id'])
            print('edited msg', e['msg_id'], 'idx', e['idx'])
        else:
            fail += 1
            print('FAIL msg', e['msg_id'], r.get('description', '')[:80])
    except urllib.error.HTTPError as ex:
        fail += 1
        try:
            desc = json.loads(ex.read().decode()).get('description', '')[:120]
        except Exception:
            desc = str(ex)[:120]
        print('ERR msg', e['msg_id'], desc)

json.dump(done, open(DONE_PATH, 'w', encoding='utf-8'))
print('done:', ok, 'fail:', fail, 'skip:', skip)
