#!/usr/bin/env python3
"""Постит один текстовый пост из очереди в канал Telegram. Прогресс — в published_content.json."""
import json, os, sys, urllib.request, urllib.parse

TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL = os.environ['CHANNEL_ID']
OWNER = os.environ['CHAT_ID']

queue = json.load(open('scripts/content_queue.json', encoding='utf-8'))
pub_path = 'scripts/published_content.json'
pub = json.load(open(pub_path, encoding='utf-8')) if os.path.exists(pub_path) else {'next': 0}

idx = pub.get('next', 0)
if idx >= len(queue):
    req = urllib.request.Request('https://api.telegram.org/bot%s/sendMessage' % TOKEN,
        data=urllib.parse.urlencode({'chat_id': OWNER, 'text': '📭 Очередь контента закончилась — нужна новая порция постов'}).encode())
    urllib.request.urlopen(req, timeout=60)
    print('queue empty, stop')
    sys.exit(0)

post = queue[idx]
data = {'chat_id': CHANNEL, 'text': post['text'],
        'reply_markup': json.dumps({'inline_keyboard': post.get('buttons', [])}, ensure_ascii=False),
        'disable_web_page_preview': 'true'}
req = urllib.request.Request('https://api.telegram.org/bot%s/sendMessage' % TOKEN,
    data=urllib.parse.urlencode(data).encode(), headers={'User-Agent': 'zapashoda-bot'})
try:
    r = json.load(urllib.request.urlopen(req, timeout=60))
    print('sent:', r.get('ok'), 'msg_id:', r.get('result', {}).get('message_id'))
    if not r.get('ok'):
        sys.exit(1)
except Exception as e:
    print('send failed:', type(e).__name__, str(e)[:200])
    sys.exit(1)

pub['next'] = idx + 1
json.dump(pub, open(pub_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('progress saved: next =', pub['next'])
