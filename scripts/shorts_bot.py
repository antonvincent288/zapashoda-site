#!/usr/bin/env python3
# Шортс-автопилот «Запас хода»: YouTube (Creative Commons) -> Telegram
# Кандидаты ищутся по темам, фильтруются: лицензия CC (легально при атрибуции),
# длительность <=61 сек, просмотры >= MIN_VIEWS. Дедуп: scripts/published.json.
import json, os, subprocess, sys, glob, time, uuid
import urllib.request, urllib.parse

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
CHANNEL_ID = '-1002316192115'          # канал
REPORT_CHAT = '108142888'              # отчёты вам в личку
MIN_VIEWS = int(os.environ.get('MIN_VIEWS', '10000'))
MAX_DUR = 61
MAX_BYTES = 48 * 1024 * 1024           # лимит Bot API ~50 МБ
HERE = os.path.dirname(os.path.abspath(__file__))
PUBLISHED = os.path.join(HERE, 'published.json')

TOPICS = [
    'электромобиль зарядка',
    'электромобиль зимой',
    'запас хода электромобиля',
    'адаптер зарядки электромобиль',
    'ev charging shorts',
    'electric car winter tips',
]

def load_pub():
    try:
        return json.load(open(PUBLISHED, encoding='utf-8'))
    except Exception:
        return {'ids': {}, 'authors': {}, 'last_topic': None, 'order': 0}

def save_pub(p):
    json.dump(p, open(PUBLISHED, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def tg(method, **params):
    url = 'https://api.telegram.org/bot%s/%s' % (TELEGRAM_TOKEN, method)
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    try:
        return json.load(urllib.request.urlopen(req, timeout=40))
    except Exception as e:
        print('tg error', method, e)
        return {'ok': False}

def ytdlp(args, timeout=240):
    return subprocess.run(['yt-dlp'] + args, capture_output=True, text=True, timeout=timeout)

def search_topic(topic):
    """flat-поиск по теме (свежее вперёд), без скачивания"""
    cmd = ['--dump-json', '--flat-playlist', '--no-playlist',
           '-I', '1:14', 'ytsearchdate14:' + topic]
    r = ytdlp(cmd, timeout=180)
    out = []
    for line in (r.stdout or '').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
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
    body = b''
    def field(name, val):
        return ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (boundary, name, val)).encode()
    body += field('chat_id', CHANNEL_ID)
    body += field('caption', caption)
    body += field('reply_markup', json.dumps(kb, ensure_ascii=False))
    body += field('supports_streaming', 'true')
    body += field('width', '720')
    body += ('--%s\r\nContent-Disposition: form-data; name="video"; filename="clip.mp4"\r\nContent-Type: video/mp4\r\n\r\n' % boundary).encode()
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
    return str(n).replace(',', ' ').replace('.0', '')

def main():
    if not TELEGRAM_TOKEN:
        print('TELEGRAM_TOKEN secret is missing'); return
    pub = load_pub()
    now = time.time()
    candidates = []
    for topic in TOPICS:
        for e in search_topic(topic):
            vid = e.get('id')
            dur = e.get('duration') or 0
            views = e.get('view_count') or 0
            if not vid or pub['ids'].get(vid):
                continue
            if dur and dur > MAX_DUR:
                continue
            if views < MIN_VIEWS:
                continue
            candidates.append({'videoId': vid, 'topic': topic, 'views': views,
                               'url': e.get('webpage_url') or ('https://www.youtube.com/shorts/' + vid)})
        time.sleep(2)
    candidates.sort(key=lambda x: -x['views'])
    print('candidates:', len(candidates))

    posted = False
    for c in candidates[:6]:
        m = full_meta(c['url'])
        if not m:
            continue
        if m.get('license') != 'Creative Commons Attribution license (reuse allowed)':
            continue
        author = m.get('uploader') or m.get('channel') or 'YouTube'
        ch = m.get('channel_id') or m.get('uploader_id') or author
        if pub['authors'].get(ch, 0) and (now - pub['authors'][ch]) < 7 * 86400:
            continue
        if pub.get('last_topic') == c['topic']:
            continue
        clip = download(c['url'], '/tmp/clip')
        if not clip:
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
                                    'views': m.get('view_count'), 'topic': c['topic'],
                                    'ts': now}
        pub['authors'][ch] = now
        pub['last_topic'] = c['topic']
        save_pub(pub)
        os.remove(clip)
        posted = True
        tg('sendMessage', chat_id=REPORT_CHAT,
           text='✅ Шортс опубликован: «%s»\nАвтор: %s · просмотры: %s\nТема: %s' % (
               short(m.get('title'), 60), author, num(m.get('view_count') or 0), c['topic']))
        break

    if not posted:
        tg('sendMessage', chat_id=REPORT_CHAT,
           text='ℹ️ Этот прогон: подходящих CC-шортсов не нашлось (порог %s просмотров, 6 тем). Очередь ждёт пополнения — порог можно снизить в secrets MIN_VIEWS.' % num(MIN_VIEWS))

if __name__ == '__main__':
    main()
