#!/usr/bin/env python3
# Шортс-автопилот v2.6 (пулы 15 inv + 8 piped, кэш рабочих инстансов) (download: invidious first) (api 180d/25, MIN_VIEWS 500, notice 72h): YouTube Creative Commons -> Telegram
# 05.11: фикс нулевых прогонов. Причины: (1) все Invidious-инстансы массово мертвы (401/SSL),
# (2) проверка лицензии yt.lemnoslife.com отключена (таймаут) — кандидаты падали на "license unknown",
# (3) yt-dlp-поиск не содержал шортс-вариаций запросов и фильтр <=61s отсекал почти всё.
# v2.1: поиск с '#shorts'-вариациями, лицензия по watch-page (надёжный маркер CC),
# MAX_DUR поднят до 3 мин (актуальный лимит Shorts), диагностика причин в отчёте, notice 1 раз в 24ч.
import json, os, subprocess, glob, time, uuid, re
import urllib.request, urllib.parse

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
YT_API_KEY = os.environ.get('YT_API_KEY', '')
CHANNEL_ID = '-1002316192115'
REPORT_CHAT = '108142888'
MIN_VIEWS = int(os.environ.get('MIN_VIEWS', '500'))
MAX_DUR = int(os.environ.get('MAX_DUR', '185'))
MAX_BYTES = 48 * 1024 * 1024
FULL_CHECK_LIMIT = 12
RUN_BUDGET = 12 * 60
NOTICE_THROTTLE = 72 * 3600
HERE = os.path.dirname(os.path.abspath(__file__))
PUBLISHED = os.path.join(HERE, 'published.json')
CC = 'Creative Commons Attribution license (reuse allowed)'

INV_INSTANCES = [
    'https://invidious.tiekoetter.com',
    'https://invidious.nerdvpn.de',
    'https://inv.nadeko.net',
    'https://yt.chocolatemoo53.com',
    'https://invidious.f5.si',
    'https://invidious.privacyredirect.com',
    'https://iv.ggtyler.dev',
    'https://invidious.materialio.us',
    'https://iv.melmac.space',
    'https://invidious.dhusch.de',
    'https://inv.vern.cc',
    'https://invidious.fdn.fr',
    'https://iv.duti.dev',
    'https://yt.artemislena.eu',
    'https://invidious.drgns.space',
]
PIPED = [
    'https://pipedapi.kavin.rocks',
    'https://pipedapi.adminforge.de',
    'https://api.piped.private.coffee',
    'https://pipedapi.leptons.xyz',
    'https://pipedapi.reallyaweso.me',
    'https://pipedapi.phoenixthrush.com',
    'https://pipedapi.owo.si',
    'https://pipedapi.moomoo.fi',
]
TOPICS = [
    'электромобиль зарядка',
    'электромобиль зимой',
    'запас хода электромобиля',
    'адаптер зарядки электромобиль',
    'зарядная станция электромобиль',
    'домашняя зарядка электромобиля',
    'ev charging shorts',
    'electric car winter',
    'ev charging tips',
    'типы разъемов зарядки',
    'ev charging',
    'tesla charging',
    'electric vehicle charging',
    'электромобиль зарядка дома',
]

def dynamic_instances():
    bases = []
    try:
        data = get_json('https://api.invidious.io/instances.json?sort_by=health', timeout=15)
        for e in data:
            if isinstance(e, list) and isinstance(e[1], dict) and e[1].get('type') == 'https' and e[1].get('api', False):
                bases.append('https://' + e[0])
    except Exception as e:
        print('  [instances list fail]', type(e).__name__)
    for b in INV_INSTANCES:
        if b not in bases:
            bases.append(b)
    return bases

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

# ---------- источник 1: Invidious (деградировавший, оставлен как best-effort) ----------
def inv_search(topic):
    q = urllib.parse.quote(topic)
    for base in INV_INSTANCES:
        try:
            data = get_json(base + '/api/v1/search?q=%s&type=video&sort_by=view_count&fields=videoId,title,author,authorId,lengthSeconds,viewCount,license' % q, timeout=15)
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
    for base in INV_INSTANCES:
        try:
            v = get_json(base + '/api/v1/videos/%s?fields=license,viewCount,title,author,authorId,formatStreams' % c['videoId'], timeout=15)
        except Exception as e:
            print('  [inv video fail] %s: %s' % (base, type(e).__name__))
            continue
        if not isinstance(v, dict) or not v.get('title'):
            continue
        info = {'license': v.get('license'), 'views': int(v.get('viewCount') or 0),
                'title': v.get('title'), 'author': v.get('author'), 'ch': v.get('authorId'),
                'stream_url': None, '_dl_base': base}
        fs = [f for f in (v.get('formatStreams') or []) if 'mp4' in (f.get('mimeType') or '')]
        if fs:
            fs.sort(key=lambda f: int(f.get('height') or 0), reverse=True)
            info['stream_url'] = fs[0].get('url')
        return info
    return None

def inv_download(c, dst):
    bases = []
    if c.get('_dl_base'): bases.append(c['_dl_base'])
    if c.get('_base') and c['_base'] not in bases: bases.append(c['_base'])
    bases += [b for b in INV_INSTANCES if b not in bases]
    tries = ([c['stream_url']] if c.get('stream_url') else [])
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
            print('  [inv dl fail]', str(url)[:80], type(e).__name__)
    return None

# ---------- источник 2: yt-dlp ----------
EXTRACTOR_FALLBACK = ['--extractor-args', 'youtube:player_client=ios,android_vr,tv_embedded']
POT_ARGS = ['--extractor-args', 'youtube:player_client=web',
            '--extractor-args', 'youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416']

def ytdlp_search(topic):
    """Поиск с вариациями запроса; flat-playlist даёт duration — фильтруем <=MAX_DUR."""
    raw, seen = [], set()
    for variant in (topic, topic + ' #shorts'):
        r = ytdlp(['--dump-json', '--flat-playlist', '--no-playlist', '-I', '1:25', 'ytsearch25:' + variant], timeout=180)
        for line in (r.stdout or '').splitlines():
            line = line.strip()
            if line:
                try: raw.append(json.loads(line))
                except Exception: pass
        time.sleep(1)
    cands = []
    for e in raw:
        vid = e.get('id')
        dur = e.get('duration') or 0
        if not vid or vid in seen or (dur and dur > MAX_DUR):
            continue
        seen.add(vid)
        cands.append({'videoId': vid, 'topic': topic, 'views': int(e.get('view_count') or 0),
                      'title': e.get('title'), 'dur': dur,
                      'url': e.get('webpage_url') or ('https://www.youtube.com/shorts/' + vid),
                      '_src': 'yt'})
    return cands

def full_meta(url):
    for extra in ([], EXTRACTOR_FALLBACK):
        r = ytdlp(['--dump-json', '--no-playlist', '--no-warnings'] + extra + [url], timeout=90)
        try:
            return json.loads((r.stdout or '').strip().splitlines()[-1])
        except Exception:
            pass
    return None

def watch_page_license(vid):
    """Лицензия по watch-page: маркер CC в HTML (замена мёртвого lemnoslife).
    Возвращает CC / 'standard' (страница отрисована, CC нет) / None (не удалось проверить)."""
    url = 'https://www.youtube.com/watch?v=' + vid
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                                                       'Accept-Language': 'en-US,en;q=0.9'})
            html = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'ignore')
            if len(html) < 20000:
                time.sleep(3)
                continue
            return CC if 'Creative Commons' in html else 'standard'
        except Exception as e:
            print('  [watch page fail]', type(e).__name__, str(e)[:90])
            time.sleep(3)
    return None

def cobalt_download(url, dst):
    """Открытые инстансы cobalt — прямая ссылка на mp4 без yt-dlp"""
    bases = []
    try:
        data = get_json('https://instances.cobalt.best/api/instances.json', timeout=20)
        for i in data if isinstance(data, list) else []:
            if i.get('api') and i.get('protocol') == 'https' and (i.get('services') or {}).get('youtube') and not i.get('turnstile'):
                b = i['api'] if i['api'].startswith('http') else 'https://' + i['api']
                if b not in bases:
                    bases.append(b)
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
                raw = urllib.request.urlopen(urllib.request.Request(dl, headers={'User-Agent': 'Mozilla/5.0'}), timeout=90).read()
                if len(raw) > 100000 and len(raw) <= MAX_BYTES:
                    open(dst, 'wb').write(raw)
                    print('  [cobalt] OK via', base, len(raw))
                    return dst
            else:
                print('  [cobalt] %s: %s %s' % (base, status, str(r.get('text'))[:100]))
        except Exception as e:
            print('  [cobalt fail] %s: %s %s' % (base, type(e).__name__, str(e)[:60]))
    return None

def ytdlp_download(url, dst):
    for extra in (POT_ARGS, [], EXTRACTOR_FALLBACK):
        r = ytdlp(['-f', 'best[ext=mp4]/best', '--no-playlist', '--no-warnings',
                   '--max-filesize', '60M', '-o', dst] + extra + [url], timeout=90)
        files = glob.glob(dst + '.*')
        if files and r.returncode == 0:
            f = files[0]
            if os.path.getsize(f) > MAX_BYTES:
                os.remove(f); return None
            return f
        if (r.stderr or '').strip():
            lines = [x for x in (r.stderr or '').strip().splitlines() if 'WARNING' not in x]
            print('  [dl] rc=%d %s' % (r.returncode, ' | '.join(lines[:6])[:500]))
            print('  [dl tail]', (r.stderr or '').strip()[-300:].replace('\n', ' | '))
    return cobalt_download(url, dst)

def qnum(q):
    digits = ''.join(ch for ch in str(q or '') if ch.isdigit())
    return int(digits) if digits else 0

def _dl(url, dst):
    req_ = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = urllib.request.urlopen(req_, timeout=90).read()
    if 100000 < len(data) <= MAX_BYTES:
        open(dst, 'wb').write(data)
        return dst
    print('  [dl] bad size', len(data))
    return None

def inv_direct_download(c, dst, pub):
    """Прямые googlevideo-URL из Invidious (formatStreams/adaptiveFormats) — без прокси инстанса."""
    cache = pub.get('ok_inv')
    bases = ([cache] if cache else []) + [b for b in INV_INSTANCES if b != cache]
    for base in bases[:6]:
        try:
            v = get_json(base + '/api/v1/videos/%s?fields=formatStreams,adaptiveFormats' % c['videoId'], timeout=12)
        except Exception:
            continue
        urls = []
        for f in (v.get('formatStreams') or []) + (v.get('adaptiveFormats') or []):
            u = f.get('url') or ''
            if 'googlevideo.com' not in u:
                continue
            mime = (f.get('container') or '') + (f.get('mimeType') or '') + u
            if 'mp4' not in mime:
                continue
            urls.append((0 if 'itag=18' in u else (1 if 'itag=22' in u else 2), u))
        if urls:
            urls.sort(key=lambda t: t[0])
            for _, u in urls[:4]:
                try:
                    if _dl(u, dst):
                        print('  [inv direct] OK via', base)
                        pub['ok_inv'] = base
                        save_pub(pub)
                        return dst
                except Exception as e:
                    print('  [inv direct fail]', type(e).__name__, str(e)[:70])
    return None

def piped_download(vid, dst, pub):
    cache = pub.get('ok_piped')
    bases = ([cache] if cache else []) + [b for b in PIPED if b != cache]
    for base in bases[:6]:
        try:
            s = get_json(base + '/streams/' + vid, timeout=15)
        except Exception as e:
            print('  [piped fail] %s: %s' % (base, type(e).__name__))
            continue
        if not s.get('title'):
            continue
        vs = [v for v in (s.get('videoStreams') or []) if v.get('url')]
        mux = [v for v in vs if not v.get('videoOnly') and 'MPEG_4' in (v.get('format') or '')]
        mux.sort(key=lambda v: -qnum(v.get('quality')))
        for v in mux[:2]:
            try:
                if _dl(v['url'], dst):
                    print('  [piped] OK via', base)
                    pub['ok_piped'] = base
                    save_pub(pub)
                    return dst
            except Exception as e:
                print('  [piped dl fail]', type(e).__name__, str(e)[:70])
        vo = [v for v in vs if v.get('videoOnly') and 'MPEG_4' in (v.get('format') or '')]
        au = [a for a in (s.get('audioStreams') or []) if a.get('url') and 'M4A' in (a.get('format') or '')]
        if vo and au:
            vo.sort(key=lambda v: -qnum(v.get('quality')))
            au.sort(key=lambda a: -qnum(a.get('quality')))
            vurl, aurl = vo[0]['url'], au[0]['url']
            try:
                open('/tmp/pv.mp4', 'wb').write(urllib.request.urlopen(urllib.request.Request(vurl, headers={'User-Agent': 'Mozilla/5.0'}), timeout=120).read())
                open('/tmp/pa.m4a', 'wb').write(urllib.request.urlopen(urllib.request.Request(aurl, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read())
                r = subprocess.run(['ffmpeg', '-y', '-i', '/tmp/pv.mp4', '-i', '/tmp/pa.m4a', '-c', 'copy', dst],
                                   capture_output=True, timeout=120)
                if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 100000 and os.path.getsize(dst) <= MAX_BYTES:
                    print('  [piped mux] OK via', base)
                    pub['ok_piped'] = base
                    save_pub(pub)
                    return dst
                print('  [piped mux fail] rc=%d' % r.returncode)
            except Exception as e:
                print('  [piped mux fail]', type(e).__name__, str(e)[:70])
    return None

# ---------- источник 3: YouTube API ----------
def api_search(topic):
    if not YT_API_KEY:
        return []
    since = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 180*86400))
    try:
        s = get_json('https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=25&type=video'
                     '&order=viewCount&relevanceLanguage=ru&videoLicense=creativeCommon'
                     '&publishedAfter=%s&q=%s&key=%s' % (since, urllib.parse.quote(topic), YT_API_KEY), timeout=30)
    except urllib.error.HTTPError as e:
        print('  [api search error] HTTP %s' % e.code)
        return []
    except Exception as e:
        print('  [api search error]', type(e).__name__, str(e)[:100]); return []
    ids = [i['id']['videoId'] for i in s.get('items', []) if i.get('id', {}).get('videoId')]
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
    """Возвращает (ok, причина-отказа)"""
    vid = c['videoId']
    if pub['ids'].get(vid):
        return False, 'already posted'
    if c['_src'] == 'inv':
        v = inv_video(c)
        if not v:
            return False, 'no usable source'
        for k in ('license', 'views', 'title', 'author', 'ch', 'stream_url', '_dl_base'):
            if k in v: c[k] = v[k]
    elif c['_src'] == 'yt':
        m = full_meta(c['url'])
        if not m:
            return False, 'full_meta failed'
        c['license'] = m.get('license')
        c['views'] = int(m.get('view_count') or 0)
        c['title'] = m.get('title')
        c['author'] = m.get('uploader') or m.get('channel')
        c['ch'] = m.get('channel_id') or m.get('uploader_id')
    lic = c.get('license')
    if not lic:
        lic = watch_page_license(vid)
        c['license'] = lic
    if lic == 'standard':
        return False, 'not CC'
    if not lic:
        return False, 'license unverified'
    if lic not in (CC, 'creativeCommon'):
        return False, 'not CC (%s)' % lic
    if c['views'] < MIN_VIEWS:
        return False, 'views %d < %d' % (c['views'], MIN_VIEWS)
    author = c.get('author') or 'YouTube'
    ch = c.get('ch') or author
    if pub['authors'].get(ch, 0) and (now - pub['authors'][ch]) < 7 * 86400:
        return False, 'author cooldown'
    if pub.get('last_topic') == c['topic']:
        return False, 'same topic as last'
    clip = None
    for attempt in (lambda: inv_direct_download(c, '/tmp/clip.mp4', pub),
                    lambda: piped_download(c['videoId'], '/tmp/clip.mp4', pub),
                    lambda: inv_download(c, '/tmp/clip.mp4') if (c.get('stream_url') or c['_src'] != 'inv') else None,
                    lambda: ytdlp_download(c['url'], '/tmp/clip')):
        try:
            clip = attempt()
        except Exception as e:
            print('  [dl attempt fail]', type(e).__name__, str(e)[:80])
        if clip:
            break
    if not clip:
        return False, 'download failed'
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
        return False, 'send failed: %s' % sent.get('description', '')
    pub['ids'][vid] = {'title': c.get('title'), 'author': author, 'views': c['views'],
                       'topic': c['topic'], 'ts': now, 'src': c['_src']}
    pub['authors'][ch] = now
    pub['last_topic'] = c['topic']
    save_pub(pub)
    tg('sendMessage', chat_id=REPORT_CHAT,
       text='✅ Шортс опубликован: «%s»\nАвтор: %s · просмотры: %s\nТема: %s\nИсточник: %s' % (
           short(c.get('title'), 60), author, num(c['views']), c['topic'], c['_src']))
    return True, 'posted'

def main():
    if not TELEGRAM_TOKEN:
        print('TELEGRAM_TOKEN secret is missing'); return
    pub = load_pub()
    now = time.time()
    INV_INSTANCES[:] = dynamic_instances()
    candidates, seen = [], set()
    stats = {'inv': 0, 'api': 0, 'yt': 0, 'too_long': 0, 'dup': 0}
    for topic in TOPICS:
        inv = [x for x in inv_search(topic) if not pub['ids'].get(x['videoId'])]
        api = api_search(topic)
        need_yt = (len(inv) + len(api)) < 5
        yt = ytdlp_search(topic) if need_yt else []
        got = inv + api + yt
        stats['inv'] += len(inv); stats['api'] += len(api); stats['yt'] += len(yt)
        print('topic %r: inv=%d api=%d ytdlp=%d -> %d' % (topic, len(inv), len(api), len(yt), len(got)))
        for c in got:
            if c['videoId'] in seen:
                stats['dup'] += 1
            else:
                seen.add(c['videoId'])
                candidates.append(c)
        time.sleep(1)
    candidates.sort(key=lambda x: -x['views'])
    print('candidates total:', len(candidates))
    posted, reason = False, ''
    rejects = {}
    deadline = time.time() + RUN_BUDGET
    for c in candidates[:FULL_CHECK_LIMIT]:
        if time.time() > deadline:
            print('  [budget] 12 мин истекли, кандидатов осталось:', len(candidates))
            break
        posted, reason = process(c, pub, now)
        if not posted:
            rejects[c['videoId']] = reason
            print('  reject %s (%s): %s' % (c['videoId'], c['_src'], reason))
        if posted:
            break
    if posted:
        return
    detail = ('Кандидатов: %d (inv=%d, api=%d, yt-dlp=%d; дублей=%d). '
              'Отсекло: %s' % (len(candidates), stats['inv'], stats['api'], stats['yt'], stats['dup'], reason or 'нет кандидатов'))
    print('empty run:', detail)
    if now - pub.get('last_empty_msg', 0) > NOTICE_THROTTLE:
        pub['last_empty_msg'] = now
        save_pub(pub)
        tg('sendMessage', chat_id=REPORT_CHAT,
           text='ℹ️ Прогон: подходящих CC-шортсов не нашлось.\n' + detail)
    else:
        print('notice suppressed (24h throttle)')

if __name__ == '__main__':
    main()
