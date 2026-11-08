#!/usr/bin/env python3
"""Постит один текстовый пост из очереди в канал Telegram. Прогресс — в published_content.json.
v2: автопостроение хэштегов — 2 тематических тега по содержимому поста + бренд-тег #запасхода.
Если в элементе очереди есть поле "tags" — используются только оно. Хэштеги не дублируются."""
import json, os, sys, urllib.request, urllib.parse

TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL = os.environ['CHANNEL_ID']
OWNER = os.environ['CHAT_ID']

BRAND_TAG = '#запасхода'
TAG_MAP = [
    (('разъём', 'разъем', 'gbt', 'gb/t', 'ccs2', 'type 2', 'type2'), '#разъёмы'),
    (('адаптер',), '#адаптеры'),
    (('зим', 'мороз'), '#зима'),
    (('батаре',), '#батарея'),
    (('домаш', 'розетка', 'удлинит'), '#домашняязарядка'),
    (('миф',), '#мифы'),
    (('простой', 'проста'), '#простой'),
    (('м-11', 'м-12', 'трасс', 'дальня', 'маршрут'), '#маршруты'),
    (('квиз', 'подбор', 'проверь', 'посмотри'), '#подбор'),
    (('эконом', 'дешев', '₽', 'стоит', 'копейки'), '#экономия'),
    (('станци', 'эзс'), '#станции'),
]

def tags_for(text, override=None):
    if override:
        return ' '.join(override[:3])
    low = text.lower()
    tags = []
    for keys, tag in TAG_MAP:
        if tag not in tags and any(k in low for k in keys):
            tags.append(tag)
        if len(tags) >= 2:
            break
    if BRAND_TAG in text[-100:].lower():
        return ''
    return ' '.join(tags + [BRAND_TAG])

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
text = post['text'].rstrip()
tags_line = tags_for(post['text'], post.get('tags'))
if tags_line:
    text = text + '\n\n' + tags_line

data = {'chat_id': CHANNEL, 'text': text,
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
