#!/usr/bin/env python3
# Шортс-автопилот v2.7 (поиск по 5 инстансам, скачивание по всему пулу) (download: invidious first) (api 180d/25, MIN_VIEWS 500, notice 72h): YouTube Creative Commons -> Telegram
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

def cookies_file():
    raw = os.environ.get('YT_COOKIES', '')
    if not raw:
        return None
    p = '/tmp/yt_cookies.txt'
    with open(p, 'w') as f:
        f.write(raw)
    return p

def ytdlp(args, timeout=240):
    extra = []
    cf = cookies_file()
    if cf:
        extra = ['--cookies', cf]
    return subprocess.run(['yt-dlp'] + extra + args, capture_output=True, text=True, timeout=timeout)

# ---------- источник 1: Invidious (деградировавший, оставлен как best-effort) ----------
def inv_search(topic):
    q = urllib.parse.quote(topic)
    for base in INV_INSTANCES[:5]:
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
    for base in INV_INSTANCES[:6]:
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
            # SABR-компаньоны инстансов (companion/sabr-segment) — НЕ прямой файл:
            # fMP4-фрагменты без moov, Telegram принимает их как «пустое» видео 0:00.
            if 'sabr-segment' in u or 'companion/' in u:
                continue
            host = urllib.parse.urlparse(u).netloc.lower()
            if not host.endswith('googlevideo.com'):
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


COOKIES_HELP = ('Чтобы я качал видео по ссылке с YouTube/Inst, нужны куки YouTube:\n'
                '1) расширение «Get cookies.txt LOCALLY» в браузере;\n'
                '2) открой youtube.com, экспортируй cookies.txt;\n'
                '3) вставь содержимое в секрет YT_COOKIES репо zapashoda-site.\n'
                'Пока куки нет: просто перешли мне сюда сам файл видео — опубликую в канале.')

def process_pending_uploads(pub):
    """Личные сообщения владельца боту:
    видео-файл -> публикация в канал с брендовой подписью;
    ссылка youtube/inst -> yt-dlp (нужен секрет YT_COOKIES).
    Апдейты подтверждаем offset-ом, чтобы не репостить повторно."""
    try:
        offset = int(pub.get('tg_offset', 0) or 0)
        req_ = urllib.request.Request('https://api.telegram.org/bot%s/getUpdates?allowed_updates=message&offset=%d' % (TELEGRAM_TOKEN, offset))
        ups = json.load(urllib.request.urlopen(req_, timeout=40))
    except Exception as e:
        print('  [uploads] getUpdates fail:', type(e).__name__, str(e)[:80])
        return
    results = ups.get('result') or []
    max_id, video_updates, link_updates = None, [], []
    for u in results:
        uid = u.get('update_id')
        if uid is not None and (max_id is None or uid > max_id):
            max_id = uid
        m = u.get('message') or {}
        chat = m.get('chat') or {}
        if str(chat.get('id')) != str(REPORT_CHAT):
            continue
        if (m.get('date') or 0) < time.time() - 2 * 86400:
            continue
        doc = m.get('document') or {}
        if m.get('video') or doc.get('mime_type', '').startswith('video/'):
            video_updates.append(m)
        elif m.get('text') and re.search(r'youtube\.com|youtu\.be|instagram\.com', m.get('text') or ''):
            link_updates.append(m)
    if video_updates:
        m = video_updates[-1]  # только самый свежий — не спамим канал
        src = m.get('video') or m.get('document')
        file_id = src.get('file_id')
        cap = (m.get('caption') or 'Видео дня').strip()
        if 'http' not in cap:
            cap = cap + '\n\nПолные гайды: https://zapashoda-ev.ru/shop/digital/'
        cap += '\n#видео #запасхода'
        r = tg('sendVideo', chat_id=CHANNEL_ID, video=file_id, caption=cap, supports_streaming='true')
        ok = bool(r.get('ok'))
        print('  [uploads] owner video -> ok=%s msg=%s' % (ok, (r.get('result') or {}).get('message_id')))
        tg('sendMessage', chat_id=REPORT_CHAT,
           text='✅ Видео опубликовано в канале.' if ok else 'Не смог опубликовать видео: %s' % (r.get('description') or 'ошибка'))
    for m in link_updates[:1]:
        url = re.search(r'https?://\S+', m.get('text') or '').group(0)
        cf = cookies_file()
        if not cf:
            tg('sendMessage', chat_id=REPORT_CHAT, text=COOKIES_HELP)
            print('  [uploads] link без YT_COOKIES — отправил инструкцию')
        else:
            mm = full_meta(url)
            title = (mm or {}).get('title') or 'Видео'
            out = '/tmp/owner_link.mp4'
            dl = ytdlp_download(url, out)
            if not dl:
                tg('sendMessage', chat_id=REPORT_CHAT, text='Не смог скачать по ссылке (YT_COOKIES есть, но YouTube отказал).')
                continue
            dl = glob.glob(out + '.*')[0] if glob.glob(out + '.*') else dl
            okv, whyv = validate_video(dl)
            if not okv:
                tg('sendMessage', chat_id=REPORT_CHAT, text='Скачанный файл битый: %s' % whyv)
                continue
            cap = '🎬 %s\n\n#видео #запасхода\n\nПолные гайды: https://zapashoda-ev.ru/shop/digital/' % title[:80]
            sent = send_video(dl, cap, {'inline_keyboard': [[{'text': '🔋 Открыть гид', 'url': 'https://t.me/zapashoda_ev_bot/app'}]]})
            print('  [uploads] link video -> ok=%s' % sent.get('ok'))
            tg('sendMessage', chat_id=REPORT_CHAT,
               text='✅ Опубликовал видео по ссылке.' if sent.get('ok') else 'Не смог опубликовать: %s' % sent.get('description', ''))
    if max_id is not None:
        pub['tg_offset'] = max_id + 1
        save_pub(pub)
        print('  [uploads] offset =', pub['tg_offset'])

# ---------- Commons: реальные CC-видео напрямую (без авторизаций) ----------
COMMONS_UA = {'User-Agent': 'zapashoda-bot/1.0 (https://zapashoda-ev.ru)'}
COMMONS_QUERIES = ['electric car charging filetype:video', 'electric vehicle charging station filetype:video',
                   'tesla supercharger filetype:video', 'electric car battery filetype:video',
                   'ev charging station filetype:video', 'electric car winter filetype:video']

def commons_api(params):
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=COMMONS_UA), timeout=30))

def commons_send_video(path, caption):
    boundary = uuid.uuid4().hex
    parts = [('--%s\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n%s\r\n' % (boundary, CHANNEL_ID)).encode(),
             ('--%s\r\nContent-Disposition: form-data; name="caption"\r\n\r\n%s\r\n' % (boundary, caption)).encode(),
             ('--%s\r\nContent-Disposition: form-data; name="supports_streaming"\r\n\r\ntrue\r\n' % boundary).encode(),
             ('--%s\r\nContent-Disposition: form-data; name="video"; filename="%s"\r\nContent-Type: video/mp4\r\n\r\n' % (boundary, os.path.basename(path))).encode(),
             open(path, 'rb').read(),
             ('\r\n--%s--\r\n' % boundary).encode()]
    req_ = urllib.request.Request('https://api.telegram.org/bot%s/sendVideo' % TELEGRAM_TOKEN,
        data=b''.join(parts), headers={'Content-Type': 'multipart/form-data; boundary=%s' % boundary})
    try:
        return json.load(urllib.request.urlopen(req_, timeout=180))
    except urllib.error.HTTPError as e:
        print('  [commons] sendVideo HTTP', e.code, e.read().decode('utf-8', 'replace')[:200])
        return {'ok': False}

def commons_short(pub):
    """Один реальный CC-ролик с Wikimedia Commons за день: поиск -> скачивание -> mp4 -> пост."""
    today = time.strftime('%Y-%m-%d', time.gmtime())
    if pub.get('last_commons_date') == today:
        print('  [commons] сегодня уже публиковали — пауза')
        return False
    used = set(pub.get('commons_used', []))
    chosen = None
    for q in COMMONS_QUERIES:
        try:
            d = commons_api({'action': 'query', 'list': 'search', 'srsearch': q, 'srnamespace': '6',
                             'srlimit': '10', 'format': 'json'})
        except Exception as e:
            print('  [commons] search fail', type(e).__name__, str(e)[:80]); continue
        for h in (d.get('query') or {}).get('search', []):
            t = h['title']
            if t in used or not t.lower().endswith(('.webm', '.mp4', '.ogv', '.mov')):
                continue
            try:
                ii = list(commons_api({'action': 'query', 'titles': t, 'prop': 'imageinfo',
                                       'iiprop': 'url|size|duration|extmetadata', 'format': 'json'})['query']['pages'].values())[0]['imageinfo'][0]
            except Exception:
                continue
            size = ii.get('size') or 0
            if size > MAX_BYTES or size < 300000:
                continue
            dur = float(ii.get('duration') or 0)
            if dur and dur > 185:
                continue
            lic = (((ii.get('extmetadata') or {}).get('LicenseShortName') or {}).get('value') or 'CC')
            chosen = {'title': t, 'url': ii['url'],
                      'page': 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(t),
                      'dur': dur, 'lic': lic}
            break
        if chosen:
            break
    if not chosen:
        print('  [commons] кандидатов нет')
        return False
    print('  [commons] выбрал:', chosen['title'], chosen['dur'], 's')
    ext = os.path.splitext(chosen['url'])[1][:5] or '.bin'
    raw = '/tmp/commons_raw' + ext
    try:
        req_ = urllib.request.Request(chosen['url'], headers=COMMONS_UA)
        with urllib.request.urlopen(req_, timeout=300) as r_, open(raw, 'wb') as f_:
            f_.write(r_.read())
    except Exception as e:
        print('  [commons] download fail', type(e).__name__, str(e)[:100])
        return False
    out = '/tmp/commons_post.mp4'
    cmd = ['ffmpeg', '-y', '-i', raw] + (['-t', '59'] if chosen['dur'] > 60 else []) + [
        '-vf', "scale='min(1080,iw)':-2", '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', out]
    r_ = subprocess.run(cmd, capture_output=True, timeout=900)
    if r_.returncode != 0:
        print('  [commons] ffmpeg fail:', r_.stderr.decode()[-200:])
        return False
    okv, dur2 = validate_video(out)
    if not okv:
        print('  [commons] файл битый:', dur2)
        return False
    clean = chosen['title'].replace('File:', '')
    for ext_ in ('.webm', '.mp4', '.ogv', '.mov'):
        clean = clean.replace(ext_, '')
    cap = ('🎬 %s\n\n📁 Источник: Wikimedia Commons · %s\n%s\n\n#видео #запасхода'
           % (clean[:70], chosen['lic'], chosen['page']))
    sent = commons_send_video(out, cap)
    msg_id = (sent.get('result') or {}).get('message_id')
    print('  [commons] sent:', sent.get('ok'), 'msg_id:', msg_id)
    if sent.get('ok'):
        pub.setdefault('commons_used', []).append(chosen['title'])
        pub['commons_used'] = pub['commons_used'][-40:]
        pub['last_commons_date'] = today
        save_pub(pub)
        return True
    return False

def validate_video(path, min_dur=2.0):
    """Валидация скачанного файла перед отправкой: видео-дорожка есть, длительность >= min_dur.
    Лечит случай SABR-потоков YouTube: инстанс отдаёт fMP4-фрагменты без moov — Telegram
    принимает их как «пустое» видео 0:00, и в канале висит нерабочий файл."""
    streams, dur = [], 0.0
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                            '-show_entries', 'stream=codec_name', '-show_entries', 'format=duration',
                            '-of', 'json', path], capture_output=True, text=True, timeout=60)
        meta = json.loads(r.stdout or '{}')
        streams = meta.get('streams') or []
        dur = float((meta.get('format') or {}).get('duration') or 0)
    except Exception:
        pass
    if not streams or dur < min_dur:
        # фолбэк: ffmpeg печатает Duration только для цельного файла с moov
        try:
            r = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:v:0', '-f', 'null', '-'],
                               capture_output=True, text=True, timeout=120)
            m = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', (r.stderr or '') + (r.stdout or ''))
            if m and r.returncode == 0:
                dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
                streams = [{'codec_name': 'video'}]
        except Exception:
            pass
    if not streams:
        return False, 'no video stream (не цельный mp4)'
    if dur < min_dur:
        return False, 'duration %.1fs < %.1fs (битый/фрагментированный файл)' % (dur, min_dur)
    return True, 'ok (%.1fs)' % dur

CLEANUP_TARGET = 'K0GV_0xE3Y8'

def cleanup_broken_posts():
    """Разовая чистка канала: удалить «пустой» шорт, отправленный из SABR-фрагмента (08.11).
    Ищем в ещё неподтверждённых апдейтах бота channel_post с видео и нашим маркером в подписи."""
    try:
        req_ = urllib.request.Request('https://api.telegram.org/bot%s/getUpdates?allowed_updates=channel_post' % TELEGRAM_TOKEN)
        ups = json.load(urllib.request.urlopen(req_, timeout=40))
    except Exception as e:
        print('  [cleanup] getUpdates fail:', type(e).__name__, str(e)[:80])
        ups = {'result': []}
    deleted = False
    for u in (ups.get('result') or []):
        cp = u.get('channel_post') or {}
        text = cp.get('caption') or cp.get('text') or ''
        if cp.get('video') and CLEANUP_TARGET in text:
            r = tg('deleteMessage', chat_id=CHANNEL_ID, message_id=cp['message_id'])
            print('  [cleanup] delete %s -> ok=%s' % (cp['message_id'], r.get('ok')))
            if r.get('ok'):
                tg('sendMessage', chat_id=REPORT_CHAT,
                   text='🧹 Удалил пустой шорт «Необычная Зарядка Теслы» (пришёл fMP4-фрагмент вместо цельного mp4). Перевыкладываю исправленный.')
            deleted = bool(r.get('ok'))
            break
    if not deleted:
        # фолбэк: известный id пустого поста (SABR-фрагмент, 08.11 19:46 UTC, «Необычная Зарядка Теслы»)
        r = tg('deleteMessage', chat_id=CHANNEL_ID, message_id=49)
        print('  [cleanup] delete by id 49 -> ok=%s %s' % (r.get('ok'), r.get('description', '')))
        deleted = bool(r.get('ok'))
    if deleted:
        tg('sendMessage', chat_id=REPORT_CHAT,
           text='🧹 Удалил пустой шорт «Необычная Зарядка Теслы» (пришёл fMP4-фрагмент вместо цельного mp4). Пайплайн доработан: теперь файл валидируется ffprobe-ом перед отправкой.')
    return deleted

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
    okv, whyv = validate_video(clip)
    if not okv:
        try: os.remove(clip)
        except Exception: pass
        print('  [validate] reject:', whyv)
        return False, 'invalid file: %s' % whyv
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
    if not pub.get('cleanup_done'):
        if cleanup_broken_posts():
            pub['cleanup_done'] = True
            save_pub(pub)
    process_pending_uploads(pub)
    INV_INSTANCES[:] = dynamic_instances()
    if commons_short(pub):
        return
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
