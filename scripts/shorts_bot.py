#!/usr/bin/env python3
# Шортс-автопилот v1.1: YouTube (Creative Commons) -> Telegram
# v1.1: (1) published.json создаётся всегда (пустые прогоны не красные);
#       (2) фильтр просмотров перенесён на этап полных метаданных (flat-search
#           часто не отдаёт view_count и терял всех кандидатов);
#       (3) диагностика по темам в логе; (4) порог по умолчанию 5000.
import json, os, subprocess, glob, time, uuid
import urllib.request, urllib.parse

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
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
               'ytsearchdate%d:%s' % (SEARCH_LIMIT, topic)], timeout=180)
    out = []
    for line in (r.stdout or '').splitlines():
        line = line.strip()
        if line:
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def full_meta(url):
    r = ytdlp(['--dump-json', '--no-playlist', '--no-warnings', url], timeout=120)
    try:
        return json.loads((r.stdout or '').strip().splitlines()[-1])
    except Exception:
        return None

def download(url, dst):
    r = ytdlp(['-f', 'best[ext=mp4]/best', '--no-playlist', '--no-warnings',
               '--max-filesize', '60M', '-o', dst, url], timeout=300)
    files = glob.glob(dst + '.*')
    if not files or r.returncode != 0:
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
    url = 'https://api.telegram.org/bot%s/sendVideo' % TELEGRAM_TOKEN
    req = urllib.request.Request(url, data=body,
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

def main():
    if not TELEGRAM_TOKEN:
        print('TELEGRAM_TOKEN secret is missing'); return
    pub = load_pub()
    now = time.time()
    candidates = []
    for topic in TOPICS:
        found = kept = 0
        for e in search_topic(topic):
            vid = e.get('id')
            if not vid or pub['ids'].get(vid):
                continue
            found += 1
            dur = e.get('duration')
            views = e.get('view_count')
            # на flat-этапе режем только по длительности; view_count тут часто None
            if dur and dur > MAX_DUR:
                continue
            candidates.append({'videoId': vid, 'topic': topic,
                               'views': views or 0,
                               'url': e.get('webpage_url') or ('https://www.youtube.com/shorts/' + vid)})
            kept += 1
        print('topic %r: flat_found=%d kept=%d' % (topic, found, kept))
        time.sleep(2)
    candidates.sort(key=lambda x: -x['views'])
    print('flat candidates total:', len(candidates))

    posted = False
    checked = 0
    for c in candidates[:FULL_CHECK_LIMIT]:
        m = full_meta(c['url'])
        if not m:
            continue
        checked += 1
        lic = m.get('license')
        views = int(m.get('view_count') or 0)
        dur = m.get('duration') or 0
        print('check %s: license=%r views=%d dur=%s' % (c['videoId'], lic, views, dur))
        if lic != CC:
            continue
        if views < MIN_VIEWS:
            continue
        if dur and dur > MAX_DUR:
            continue
        author = m.get('uploader') or m.get('channel') or 'YouTube'
        ch = m.get('channel_id') or m.get('uploader_id') or author
        if pub['authors'].get(ch, 0) and (now - pub['authors'][ch]) < 7 * 86400:
            continue
        if pub.get('last_topic') == c['topic']:
            continue
        clip = download(c['url'], '/tmp/clip')
        if not clip:
            print('download failed for', c['videoId'])
            continue
        caption = ('🎬 ' + short(m.get('title'), 80) + '\n\n'
                   '📺 Автор: ' + author + ' · лицензия Creative Commons\n'
                   + c['url'] + '\n\n#видео #ev')
        kb = {'inline_keyboard': [[
            {'text': '📺 Оригинал на YouTube', 'url': c['url']},
            {'text': '🔋 Открыть гид', 'url': 'https://t.me/zapashoda_ev_bot/app'}
        ]]}
        sent = send_video(clip, caption, kb)
        if not sent.get('ok'):
            print('send failed for', c['videoId'], sent.get('description'))
            continue
        pub['ids'][c['videoId']] = {'title': m.get('title'), 'author': author,
                                    'views': views, 'topic': c['topic'], 'ts': now}
        pub['authors'][ch] = now
        pub['last_topic'] = c['topic']
        save_pub(pub)
        os.remove(clip)
        posted = True
        tg('sendMessage', chat_id=REPORT_CHAT,
           text='✅ Шортс опубликован: «%s»\nАвтор: %s · просмотры: %s\nТема: %s' % (
               short(m.get('title'), 60), author, num(views), c['topic']))
        break

    print('checked full meta:', checked, '| posted:', posted)
    if not posted:
        tg('sendMessage', chat_id=REPORT_CHAT,
           text='ℹ️ Прогон: подходящих CC-шортсов не нашлось (порог %s просмотров). Снижаем порог или расширяем темы — см. секрет MIN_VIEWS и TOPICS в скрипте.' % num(MIN_VIEWS))
    # published.json должен существовать всегда — иначе commit-шаг красный
    if not os.path.exists(PUBLISHED):
        save_pub(pub)

if __name__ == '__main__':
    main()
