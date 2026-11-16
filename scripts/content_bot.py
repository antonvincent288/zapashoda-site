#!/usr/bin/env python3
"""Постит один пост из очереди в канал Telegram (HTML-формат по скиллу telegram-growth-expert).
Прогресс — в published_content.json."""
import json, os, sys, urllib.request, urllib.parse

TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL = os.environ['CHANNEL_ID']
OWNER = os.environ['CHAT_ID']


def esc(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def fmt(post: dict) -> str:
    """Оформление поста: жирный заголовок, хук ≤2 строк, пункты, хэштеги."""
    lines = post['text'].split('\n')
    html = '<b>%s</b>' % esc(lines[0].strip())
    rest = '\n'.join(lines[1:]).strip()
    if rest:
        html += '\n\n' + esc(rest)
    tags = post.get('tags') or []
    if tags:
        html += '\n\n' + ' '.join(esc(t) for t in tags)
    return html


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
data = {'chat_id': CHANNEL,
        'text': post.get('html') or fmt(post),
        'parse_mode': 'HTML',
        'reply_markup': json.dumps({'inline_keyboard': (lambda b: ([[{'text': '📖 Читать статью', 'url': post['link']}]] + [x for x in b if x]) if post.get('link') and not any(post['link'] in r[0].get('url','') for r in b) else b)(post.get('buttons', []))}, ensure_ascii=False),
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

try:
    msg_id = r.get('result', {}).get('message_id')
    ids = pub.setdefault('ids', {})
    ids[str(idx)] = msg_id
    if msg_id:
        print('tracked msg_id', msg_id, 'for idx', idx)
except Exception:
    pass

pub['next'] = idx + 1
json.dump(pub, open(pub_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('progress saved: next =', pub['next'])
