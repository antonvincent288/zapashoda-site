#!/usr/bin/env python3
"""Бэкфилл старых постов канала: добавляет хэштеги и жирный заголовок (editMessageText).
Маппинг: scripts/backfill_map.json. Идемпотентен: пройденные msg_id пишутся в scripts/backfill_done.json."""
import json, os, sys, urllib.request, urllib.parse

TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL = os.environ['CHANNEL_ID']

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def fmt(text, tags):
    lines = text.split('\n')
    html = '<b>%s</b>' % esc(lines[0].strip())
    rest = '\n'.join(lines[1:]).strip()
    if rest:
        html += '\n\n' + esc(rest)
    if tags:
        html += '\n\n' + ' '.join(esc(t) for t in tags)
    return html

items = json.load(open('scripts/backfill_map.json', encoding='utf-8'))
done_path = 'scripts/backfill_done.json'
done = json.load(open(done_path, encoding='utf-8')) if os.path.exists(done_path) else []

ok = fail = 0
for item in items:
    mid = item['msg_id']
    if mid in done:
        continue
    data = {
        'chat_id': CHANNEL,
        'message_id': mid,
        'text': fmt(item['text'], item.get('tags', [])),
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'true',
    }
    if item.get('buttons'):
        data['reply_markup'] = json.dumps({'inline_keyboard': item['buttons']}, ensure_ascii=False)
    req = urllib.request.Request('https://api.telegram.org/bot%s/editMessageText' % TOKEN,
        data=urllib.parse.urlencode(data).encode(), headers={'User-Agent': 'zapashoda-bot'})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=60))
        if r.get('ok'):
            ok += 1
            done.append(mid)
            print('edited msg', mid, 'ok')
        else:
            fail += 1
            print('msg', mid, 'error:', r.get('description'))
    except Exception as e:
        fail += 1
        print('msg', mid, 'exception:', type(e).__name__, str(e)[:120])

json.dump(done, open(done_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'итого: отредактировано {ok}, ошибок {fail}')
