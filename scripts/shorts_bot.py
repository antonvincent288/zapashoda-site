#!/usr/bin/env python3
# Шортс-автопилот v1.2: YouTube (Creative Commons) -> Telegram
# Путь 1: yt-dlp ytsearchdate (может блокироваться антиботом на CI — тогда путь 2).
# Путь 2: YouTube Data API v3 (секрет YT_API_KEY) — надёжный, с фильтром license=creativeCommon.
import json, os, subprocess, glob, time, uuid
import urllib.request, urllib.parse

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
YT_API_KEY = os.environ.get('YT_API_KEY', '')
CHANNEL_ID = '-1002316192115'
REPORT_CHAT = '108142888'
MIN_VIEWS = int(os.environ.get('MIN_VIEWS', '5000'))
MAX_DUR = 61
MAX_BYTES = 48 * 1024 * 1024
SEARCH_LIMIT = 20
FULL_CHECK_LIMIT = 8
HERE = os.path.dirname(os.path.abspath(__file__))
PUBLISHED = os.path.join(HERE, 'published.json')
CC = 'Creative Commons Attribution license (reuse allowed)'

TOPICS = [
    'электромобиль зарядка',
    'электромобиль зимой',
    'запас хода электромобиля',
    'адаптер зарядки электромобиль',
    'ev charging shorts',
    'electric car winter',
]

def load_pub():
    try:
        return json.load(open(PUBLISHED, encoding='utf-8'))
    except Exception:
        return {'ids': {}, 'authors': {}, 'last_topic': None}

def save_pub(p):
    json.dump(p, open(PUBLISHED, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def tg(method, **params):
    url = 'https://api.telegram.org/bot%s/%s' % (TELEGRAM_TOKEN, method)
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode())
    try:
        return json.load(urllib.request.urlopen(req, timeout=40))
    except Exception as e:
        print('tg error', method, e)
        return {'ok': False}

def ytdlp(args, timeout=240):
    return subprocess.run(['yt-dlp'] + args, capture_output=True, text=True, timeout=timeout)

def search_topic(topic):
    r = ytdlp(['--dump-json', '--flat-playlist', '--no-playlist', '-I', '1:%d' % SEARCH_LIMIT,
               'ytsearch%d:%s' % (SEARCH_LIMIT, topic)], timeout=180)
    out = []
    for line in (r.stdout or '').splitlines():
        line = line.strip()
        if line:
            try: out.append(json.loads(line))
            except Exception: pass
    if not out and (r.stderr or '').strip():
        print('  [search diag]', (r.stderr or '').strip()[-400:].replace('\n', ' | '))
    return out

def full_meta(url):
    r = ytdlp(['--dump-json', '--no-playlist', '--no-warnings', url], timeout=120)
    try:
        return json.loads((r.stdout or '').strip().splitlines()[-1])
    except Exception:
        return None

def api_search(topic):
    """YouTube Data API: только CC, только шортсы, с реальными просмотрами."""
    if not YT_API_KEY:
        return []
    since = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 10*86400))
    url = ('https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=10&type=video'
           '&order=viewCount&relevanceLanguage=ru&regionCode=RU&videoLicense=creativeCommon'
           '&publishedAfter=%s&q=%s&key=%s' % (since, urllib.parse.quote(topic), YT_API_KEY))
    try:
        s = json.load(urllib.request.urlopen(urllib.request.Request(url), timeout=30))
    except Exception as e:
        print('  [api search error]', topic, e)
        return []
    ids = [i['id']['videoId'] for i in s.get('items', []) if i.get('id', {}).get('videoId')]
    if not ids:
        return []
    try:
        v = json.load(urllib.request.urlopen(urllib.request.Request(
            'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,status,contentDetails&id=%s&key=%s' % (','.join(ids), YT_API_KEY)), timeout=30))
    except Exception as e:
        print('  [api videos error]', e)
        return []
    out = []
    for it in v.get('items', []):
        if (it.get('status') or {}).get('license') != 'creativeCommon':
            continue
        dur = it.get('contentDetails', {}).get('duration') or 'PT0S'
        import re
        m = re.match(r'PT(?:(\d+)M)?(?:(\d+)S)?', dur)
        secs = (int(m.group(1) or 0)*60 if m else 0) + (int(m.group(2) or 0) if m else 0)
        if secs and secs > MAX_DUR:
            continue
        out.append({'videoId': it['id'], 'topic': topic,
                    'views': int((it.get('statistics') or {}).get('viewCount') or 0),
                    'title': it.get('snippet', {}).get('title'),
                    'author': it.get('snippet', {}).get('channelTitle'),
                    'url': 'https://www.youtube.com/shorts/' + it['id'],
                    '_api': True})
    return out

def download(url, dst):
    r = ytdlp(['-f', 'best[ext=mp4]/best', '--no-playlist', '--no-warnings',
               '--max-filesize', '60M', '-o', dst, url], timeout=300)
    files = glob.glob(dst + '.*')
    if not files or r.returncode != 0:
        if (r.stderr or '').strip():
            print('  [download diag]', (r.stderr or '').strip()[-300:].replace('\n', ' | '))
        return None
    f = files[0]
    if os.path.getsize(f) > MAX_BYTES:
        os.remove(f)
        return None
    return f

def send_video(path, caption, kb):
    boundary = uuid.uuid4().hex
    def field(name, val):
        return ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (boundary, name, val)).encode()
    body = field('chat_id', CHANNEL_ID) + field('caption', caption) \
         + field('reply_markup', json.dumps(kb, ensure_ascii=False)) \
         + field('supports_streaming', 'true') \
         + ('--%s\r\nContent-Disposition: form-data; name="video"; filename="clip.mp4"\r\nContent-Type: video/mp4\r\n\r\n' % boundary).encode()
    body += open(path, 'rb').read() + ('\r\n--%s--\r\n' % boundary).encode()
    req = urllib.request.Request('https://api.telegram.org/bot%s/sendVideo' % TELEGRAM_TOKEN, data=body,
        headers={'Content-Type': 'multipart/form-data; boundary=%s' % boundary})
    try:
        return json.load(urllib.request.urlopen(req, timeout=180))
    except Exception as e:
        print('sendVideo error:', e)
        return {'ok': False}

def short(s, n):
    s = str(s or '')
    return s if len(s) <= n else s[:n-1] + '…'

def num(n):
    return str(n).replace(',', ' ')

def process(c, pub, now):
    vid = c['videoId']
    if pub['ids'].get(vid) or c['views'] < MIN_VIEWS:
        return False
    if c.get('_api'):
        m = None
    else:
        m = full_meta(c['url'])
        if not m:
            print('full_meta failed for', vid)
            return False
        print('check %s: license=%r views=%d dur=%s' % (vid, m.get('license'), int(m.get('view_count') or 0), m.get('duration')))
        if m.get('license') != CC:
            return False
        c['views'] = int(m.get('view_count') or 0)
        c['title'] = m.get('title')
        author = m.get('uploader') or m.get('channel') or 'YouTube'
        ch = m.get('channel_id') or m.get('uploader_id') or author
    author = c.get('author') or (m.get('uploader') if m else 'YouTube')
    ch = c.get('_ch') or (m.get('channel_id') if m else None) or author
    if pub['authors'].get(ch, 0) and (now - pub['authors'][ch]) < 7 * 86400:
        return False
    if pub.get('last_topic') == c['topic']:
        return False
    clip = download(c['url'], '/tmp/clip')
    if not clip:
        print('download failed for', vid)
        return False
    caption = ('🎬 ' + short(c.get('title'), 80) + '\n\n'
               '📺 Автор: ' + (author or 'YouTube') + ' · лицензия Creative Commons\n'
               + c['url'] + '\n\n#видео #ev')
    kb = {'inline_keyboard': [[
        {'text': '📺 Оригинал на YouTube', 'url': c['url']},
        {'text': '🔋 Открыть гид', 'url': 'https://t.me/zapashoda_ev_bot/app'}
    ]]}
    sent = send_video(clip, caption, kb)
    if not sent.get('ok'):
        print('send failed for', vid, sent.get('description'))
        return False
    pub['ids'][vid] = {'title': c.get('title'), 'author': author, 'views': c['views'],
                       'topic': c['topic'], 'ts': now}
    pub['authors'][ch] = now
    pub['last_topic'] = c['topic']
    save_pub(pub)
    try: os.remove(clip)
    except Exception: pass
    tg('sendMessage', chat_id=REPORT_CHAT,
       text='✅ Шортс опубликован: «%s»\nАвтор: %s · просмотры: %s\nТема: %s' % (
           short(c.get('title'), 60), author, num(c['views']), c['topic']))
    return True

def main():
    if not TELEGRAM_TOKEN:
        print('TELEGRAM_TOKEN secret is missing'); return
    pub = load_pub()
    now = time.time()
    candidates = []
    for topic in TOPICS:
        items = []
        flat = search_topic(topic)
        for e in flat:
            vid = e.get('id')
            if not vid or pub['ids'].get(vid):
                continue
            dur = e.get('duration')
            if dur and dur > MAX_DUR:
                continue
            items.append({'videoId': vid, 'topic': topic, 'views': e.get('view_count') or 0,
                          'title': e.get('title'), 'url': e.get('webpage_url') or ('https://www.youtube.com/shorts/' + vid)})
        if not flat and YT_API_KEY:
            items = [x for x in api_search(topic) if not pub['ids'].get(x['videoId'])]
        print('topic %r: flat=%d candidates=%d' % (topic, len(flat), len(items)))
        candidates += items
        time.sleep(2)
    candidates.sort(key=lambda x: -x['views'])
    print('candidates total:', len(candidates))

    posted = False
    for c in candidates[:FULL_CHECK_LIMIT]:
        if process(c, pub, now):
            posted = True
            break
    print('posted:', posted)
    if not posted:
        msg = 'ℹ️ Прогон: подходящих CC-шортсов не нашлось.'
        if not YT_API_KEY:
            msg += '\nПохоже, YouTube блокирует поиск без API-ключа на серверах GitHub. Добавьте секрет YT_API_KEY (бесплатный, 5 минут: console.cloud.google.com → проект → YouTube Data API v3 → Enable → API key) — после этого бот будет находить самые виральные CC-шортсы стабильно.'
        else:
            msg += ' Порог: %s. Можно снизить секретом MIN_VIEWS.' % num(MIN_VIEWS)
        tg('sendMessage', chat_id=REPORT_CHAT, text=msg)
    if not os.path.exists(PUBLISHED):
        save_pub(pub)

if __name__ == '__main__':
    main()
