#!/usr/bin/env python3
# Шортс-автопилот v2.0: YouTube Creative Commons -> Telegram
# Каскад источников: 1) Invidious API (поиск по просмотрам, лицензия, прямые mp4)
# 2) yt-dlp (с фоллбеками player_client) 3) YouTube Data API (секрет YT_API_KEY)
import json, os, subprocess, glob, time, uuid, re
import urllib.request, urllib.parse

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
YT_API_KEY = os.environ.get('YT_API_KEY', '')
CHANNEL_ID = '-1002316192115'
REPORT_CHAT = '108142888'
MIN_VIEWS = int(os.environ.get('MIN_VIEWS', '5000'))
MAX_DUR = 61
MAX_BYTES = 48 * 1024 * 1024
FULL_CHECK_LIMIT = 8
HERE = os.path.dirname(os.path.abspath(__file__))
PUBLISHED = os.path.join(HERE, 'published.json')
CC = 'Creative Commons Attribution license (reuse allowed)'

INV_INSTANCES = [
    'https://invidious.tiekoetter.com',
    'https://invidious.nerdvpn.de',
    'https://inv.nadeko.net',
    'https://yt.chocolatemoo53.com',
    'https://invidious.f5.si',
]
TOPICS = [
    'электромобиль зарядка',
    'электромобиль зимой',
    'запас хода электромобиля',
    'адаптер зарядки электромобиль',
    'ev charging shorts',
    'electric car winter',
]

def dynamic_instances():
    bases = []
    try:
        data = get_json('https://api.invidious.io/instances.json?sort_by=health', timeout=15)
        for e in data:
            if isinstance(e, list) and isinstance(e[1], dict) and e[1].get('type') == 'https' and e[1].get('api', True):
                bases.append('https://' + e[0])
    except Exception as e:
        print('  [instances list fail]', type(e).__name__)
    for b in INV_INSTANCES:
        if b not in bases:
            bases.append(b)
    return bases

def lemnos_license(vid):
    """Unofficial YouTube API (yt.lemnoslife.com) без ключа — status.license"""
    try:
        v = get_json('https://yt.lemnoslife.com/youtube/v3/videos?part=status,statistics,contentDetails,snippet&id=%s' % vid, timeout=25)
        it = (v.get('items') or [{}])[0]
        st = it.get('status') or {}
        lic = st.get('license')
        if lic == 'creativeCommon':
            return CC
        return lic
    except Exception as e:
        print('  [lemnos fail]', type(e).__name__, str(e)[:90])
        return None

def load_pub():
    try:
        return json.load(open(PUBLISHED, encoding='utf-8'))
    except Exception:
        return {'ids': {}, 'authors': {}, 'last_topic': None}

def save_pub(p):
    json.dump(p, open(PUBLISHED, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)', 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

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

# ---------- источник 1: Invidious ----------
def inv_search(topic):
    q = urllib.parse.quote(topic)
    for base in INV_INSTANCES:
        try:
            data = get_json(base + '/api/v1/search?q=%s&type=video&sort_by=view_count&fields=videoId,title,author,authorId,lengthSeconds,viewCount,license' % q, timeout=20)
            out = []
            for i in data:
                if not isinstance(i, dict) or not i.get('videoId'):
                    continue
                if i.get('lengthSeconds') and i['lengthSeconds'] > MAX_DUR:
                    continue
                out.append({'videoId': i['videoId'], 'topic': topic,
                            'views': int(i.get('viewCount') or 0),
                            'title': i.get('title'), 'author': i.get('author'),
                            'ch': i.get('authorId'), 'license': i.get('license'),
                            'url': 'https://www.youtube.com/shorts/' + i['videoId'],
                            '_src': 'inv', '_base': base})
            return out
        except Exception as e:
            print('  [inv search fail] %s: %s' % (base, type(e).__name__))
    return []

def inv_video(c):
    info = None
    for base in INV_INSTANCES:
        try:
            v = get_json(base + '/api/v1/videos/%s?fields=license,viewCount,title,author,authorId,formatStreams' % c['videoId'], timeout=20)
        except Exception as e:
            print('  [inv video fail] %s: %s %s' % (base, type(e).__name__, str(e)[:80]))
            continue
        if not isinstance(v, dict) or not v.get('title'):
            print('  [inv video] %s: bad response' % base)
            continue
        info = {'license': v.get('license'), 'views': int(v.get('viewCount') or 0),
                'title': v.get('title'), 'author': v.get('author'), 'ch': v.get('authorId'),
                'stream_url': None, '_dl_base': base}
        fs = [f for f in (v.get('formatStreams') or []) if 'mp4' in (f.get('mimeType') or '')]
        if fs:
            fs.sort(key=lambda f: int(f.get('height') or 0), reverse=True)
            info['stream_url'] = fs[0].get('url')
            info['itag'] = fs[0].get('itag')
            print('  [inv video] %s: OK itag %s %s (with stream)' % (base, fs[0].get('itag'), fs[0].get('qualityLabel')))
        else:
            print('  [inv video] %s: metadata OK, no stream (license=%r views=%s) — fallback to yt-dlp' % (base, info['license'], info['views']))
        break
    return info

def inv_download(c, dst):
    bases = []
    if c.get('_dl_base'):
        bases.append(c['_dl_base'])
    if c.get('_base'):
        bases.append(c['_base'])
    bases += [b for b in INV_INSTANCES if b not in bases]
    tries = [c['stream_url']]
    tries += [b + '/latest_version?id=%s&itag=18&local=true' % c['videoId'] for b in bases]
    for url in tries:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, timeout=300).read()
            if len(data) > MAX_BYTES or len(data) < 100000:
                print('  [inv dl] bad size', len(data)); continue
            open(dst, 'wb').write(data)
            return dst
        except Exception as e:
            print('  [inv dl fail]', str(url)[:90], type(e).__name__, str(e)[:80])
    return None

# ---------- источник 2: yt-dlp ----------
EXTRACTOR_FALLBACK = ['--extractor-args', 'youtube:player_client=ios,android_vr,tv_embedded']
POT_ARGS = ['--extractor-args', 'youtube:player_client=web',
            '--extractor-args', 'youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416']

def ytdlp_search(topic):
    r = ytdlp(['--dump-json', '--flat-playlist', '--no-playlist', '-I', '1:20', 'ytsearch20:' + topic], timeout=180)
    out = []
    for line in (r.stdout or '').splitlines():
        line = line.strip()
        if line:
            try: out.append(json.loads(line))
            except Exception: pass
    if not out and (r.stderr or '').strip():
        print('  [ytdlp search diag]', (r.stderr or '').strip()[-300:].replace('\n', ' | '))
    cands = []
    for e in out:
        vid = e.get('id')
        dur = e.get('duration')
        if not vid or (dur and dur > MAX_DUR):
            continue
        cands.append({'videoId': vid, 'topic': topic, 'views': e.get('view_count') or 0,
                      'title': e.get('title'), 'url': e.get('webpage_url') or ('https://www.youtube.com/shorts/' + vid),
                      '_src': 'yt'})
    return cands

def full_meta(url):
    for extra in ([], EXTRACTOR_FALLBACK, POT_ARGS):
        r = ytdlp(['--dump-json', '--no-playlist', '--no-warnings'] + extra + [url], timeout=150)
        try:
            return json.loads((r.stdout or '').strip().splitlines()[-1])
        except Exception:
            if (r.stderr or '').strip():
                print('  [meta diag]', (r.stderr or '').strip()[-250:].replace('\n', ' | '))
    return None

def cobalt_download(url, dst):
    """Открытые инстансы cobalt — прямая ссылка на mp4 без yt-dlp"""
    bases = []
    try:
        data = get_json('https://instances.cobalt.best/api/instances.json', timeout=20)
        for i in data if isinstance(data, list) else []:
            if i.get('api') and i.get('protocol') == 'https' and (i.get('services') or {}).get('youtube') and not i.get('turnstile'):
                bases.append('https://' + i['api'].lstrip('https://') if not i['api'].startswith('http') else i['api'])
    except Exception as e:
        print('  [cobalt list fail]', type(e).__name__)
    bases += ['https://api.cobalt.tools', 'https://api.cobalt.best']
    for base in bases[:6]:
        try:
            body = json.dumps({'url': url, 'videoQuality': '480', 'filenameStyle': 'basic'}).encode()
            req = urllib.request.Request(base + '/', data=body,
                headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
            r = json.load(urllib.request.urlopen(req, timeout=60))
            status = r.get('status')
            dl = r.get('url')
            if status in ('redirect', 'tunnel', 'stream') and dl:
                raw = urllib.request.urlopen(urllib.request.Request(dl, headers={'User-Agent': 'Mozilla/5.0'}), timeout=300).read()
                if len(raw) > 100000 and len(raw) <= MAX_BYTES:
                    open(dst, 'wb').write(raw)
                    print('  [cobalt] OK via', base, len(raw))
                    return dst
                print('  [cobalt] %s: bad size %d' % (base, len(raw)))
            else:
                print('  [cobalt] %s: %s %s' % (base, status, str(r.get('text'))[:80]))
        except Exception as e:
            print('  [cobalt fail] %s: %s %s' % (base, type(e).__name__, str(e)[:80]))
    return None

def ytdlp_download(url, dst):
    for extra in (POT_ARGS, [], EXTRACTOR_FALLBACK):
        r = ytdlp(['-f', 'best[ext=mp4]/best', '--no-playlist', '--no-warnings',
                   '--max-filesize', '60M', '-o', dst] + extra + [url], timeout=300)
        files = glob.glob(dst + '.*')
        if files and r.returncode == 0:
            f = files[0]
            if os.path.getsize(f) > MAX_BYTES:
                os.remove(f); return None
            return f
        if (r.stderr or '').strip():
            st = (r.stderr or '').strip()
            print('  [dl head]', ' || '.join([x for x in st.splitlines()[:14] if 'WARNING' not in x])[:600])
            print('  [dl tail]', st[-400:].replace('\n', ' | '))
    return cobalt_download(url, dst)

# ---------- источник 3: YouTube API ----------
def api_search(topic):
    if not YT_API_KEY:
        return []
    since = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 30*86400))
    try:
        s = get_json('https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=10&type=video'
                     '&order=viewCount&relevanceLanguage=ru&videoLicense=creativeCommon'
                     '&publishedAfter=%s&q=%s&key=%s' % (since, urllib.parse.quote(topic), YT_API_KEY), timeout=30)
    except urllib.error.HTTPError as e:
        print('  [api search error] HTTP %s: %s' % (e.code, e.read()[:250].decode('utf-8','replace')))
        return []
    except Exception as e:
        print('  [api search error]', type(e).__name__, str(e)[:120]); return []
    total = s.get('pageInfo', {}).get('totalResults')
    ids = [i['id']['videoId'] for i in s.get('items', []) if i.get('id', {}).get('videoId')]
    if not ids:
        print('  [api search] topic=%r totalResults=%s region=%s — CC за 10 дней не нашлось' % (topic, total, 'RU'))
        return []
    if not ids:
        return []
    try:
        v = get_json('https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,status,contentDetails&id=%s&key=%s' % (','.join(ids), YT_API_KEY), timeout=30)
    except Exception:
        return []
    out = []
    for it in v.get('items', []):
        if (it.get('status') or {}).get('license') != 'creativeCommon':
            continue
        dur = it.get('contentDetails', {}).get('duration') or 'PT0S'
        m = re.match(r'PT(?:(\d+)M)?(?:(\d+)S)?', dur)
        secs = (int(m.group(1) or 0)*60 if m else 0) + (int(m.group(2) or 0) if m else 0)
        if secs and secs > MAX_DUR:
            continue
        out.append({'videoId': it['id'], 'topic': topic,
                    'views': int((it.get('statistics') or {}).get('viewCount') or 0),
                    'title': it.get('snippet', {}).get('title'),
                    'author': it.get('snippet', {}).get('channelTitle'),
                    'ch': (it.get('snippet') or {}).get('channelId'),
                    'license': 'creativeCommon',
                    'url': 'https://www.youtube.com/shorts/' + it['id'],
                    '_src': 'api'})
    return out

# ---------- отправка ----------
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
    if pub['ids'].get(vid):
        return False
    if c['_src'] == 'inv':
        v = inv_video(c)
        if not v:
            print('no usable source for', vid); return False
        for k in ('license', 'views', 'title', 'author', 'ch', 'stream_url', 'itag', '_dl_base'):
            if k in v:
                c[k] = v[k]
    elif c['_src'] == 'yt':
        m = full_meta(c['url'])
        if not m:
            print('full_meta failed for', vid); return False
        c['license'] = m.get('license'); c['views'] = int(m.get('view_count') or 0)
        c['title'] = m.get('title'); c['author'] = m.get('uploader') or m.get('channel')
        c['ch'] = m.get('channel_id') or m.get('uploader_id')
    # api-кандидаты приходят с уже проверенной лицензией creativeCommon
    lic = c.get('license')
    if not lic:
        lic = lemnos_license(vid)
        c['license'] = lic
    if lic and lic not in (CC, 'creativeCommon'):
        print('skip %s: license=%r' % (vid, lic)); return False
    if not lic:
        print('skip %s: license unknown (не подтверждена CC)' % vid); return False
    if c['views'] < MIN_VIEWS:
        print('skip %s: views %d < %d' % (vid, c['views'], MIN_VIEWS)); return False
    author = c.get('author') or 'YouTube'
    ch = c.get('ch') or author
    if pub['authors'].get(ch, 0) and (now - pub['authors'][ch]) < 7 * 86400:
        return False
    if pub.get('last_topic') == c['topic']:
        return False
    if c['_src'] == 'inv' and c.get('stream_url'):
        clip = inv_download(c, '/tmp/clip.mp4')
    else:
        clip = ytdlp_download(c['url'], '/tmp/clip')
    if not clip:
        print('download failed for', vid)
        return False
    caption = ('🎬 ' + short(c.get('title'), 80) + '\n\n'
               '📺 Автор: ' + author + ' · лицензия Creative Commons\n'
               + c['url'] + '\n\n#видео #ev')
    kb = {'inline_keyboard': [[
        {'text': '📺 Оригинал на YouTube', 'url': c['url']},
        {'text': '🔋 Открыть гид', 'url': 'https://t.me/zapashoda_ev_bot/app'}
    ]]}
    sent = send_video(clip, caption, kb)
    try: os.remove(clip)
    except Exception: pass
    if not sent.get('ok'):
        print('send failed for', vid, sent.get('description'))
        return False
    pub['ids'][vid] = {'title': c.get('title'), 'author': author, 'views': c['views'],
                       'topic': c['topic'], 'ts': now, 'src': c['_src']}
    pub['authors'][ch] = now
    pub['last_topic'] = c['topic']
    save_pub(pub)
    tg('sendMessage', chat_id=REPORT_CHAT,
       text='✅ Шортс опубликован: «%s»\nАвтор: %s · просмотры: %s\nТема: %s\nИсточник: %s' % (
           short(c.get('title'), 60), author, num(c['views']), c['topic'], c['_src']))
    return True

def main():
    if not TELEGRAM_TOKEN:
        print('TELEGRAM_TOKEN secret is missing'); return
    pub = load_pub()
    now = time.time()
    INV_INSTANCES[:] = dynamic_instances()
    candidates = []
    for topic in TOPICS:
        inv = [x for x in inv_search(topic) if not pub['ids'].get(x['videoId'])]
        api = api_search(topic)
        yt = ytdlp_search(topic) if (not inv and not api) else []
        got = inv + api + yt
        print('topic %r: inv=%d api=%d ytdlp=%d -> %d' % (topic, len(inv), len(api), len(yt), len(got)))
        candidates += got
        time.sleep(1)
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
        tg('sendMessage', chat_id=REPORT_CHAT, text=msg)
    if not os.path.exists(PUBLISHED):
        save_pub(pub)

if __name__ == '__main__':
    main()
