#!/usr/bin/env python3
"""Реальный шортс-конвейер через ботов-скачивалок (как делают вручную):
1) YouTube Data API ищет релевантные CC-видео (поисковый спрос и лицензия — фильтры),
2) MTProto-аккаунт отправляет ссылку боту-скачивалке (@SaveAsBot и запасные),
3) забирает готовый файл, валидирует ffprobe-ом,
4) публикует в канал нашим ботом с брендовой подписью и хэштегами.
Дедуп — scripts/published.json (общий с shorts_bot).

Нужен MTProto-сеанс: секреты TG_API_ID, TG_API_HASH, TG_SESSION (StringSession).
Если их нет — бот пришлёт владельцу инструкцию настройки.
"""
import os, re, json, time, uuid, subprocess
import urllib.request, urllib.parse, urllib.error

API_ID = os.environ.get('TG_API_ID', '')
API_HASH = os.environ.get('TG_API_HASH', '')
SESSION = os.environ.get('TG_SESSION', '')
TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL = os.environ.get('CHANNEL_ID', '-1002316192115')
OWNER = os.environ.get('CHAT_ID', '108142888')
YT_API_KEY = os.environ.get('YT_API_KEY', '')
MIN_VIEWS = int(os.environ.get('MIN_VIEWS', '500'))
DL_BOTS = [b for b in os.environ.get('TG_DL_BOTS', 'SaveAsBot,Creoscanbot,TashiVideoBot,VideoGrabberYT_Bot').split(',') if b]
MAX_BYTES = 48 * 1024 * 1024
HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(HERE, 'published.json')

TOPICS = ['электромобиль зарядка', 'электромобиль зимой', 'запас хода электромобиля',
          'адаптер зарядки электромобиль', 'зарядная станция электромобиль',
          'домашняя зарядка электромобиля', 'типы разъемов зарядки', 'electric car winter',
          'tesla charging', 'ev charging tips']

SETUP_MSG = ('⚙️ Авто-скачивание через ботов-скачивалок (@SaveAsBot и запасные) готово в коде, '
             'нужен один раз MTProto-вход:\n'
             '1) my.telegram.org → API development tools → получи api_id и api_hash\n'
             '2) пришли мне сюда: api_id, api_hash и свой номер телефона\n'
             '3) я запущу вход — Telegram пришлёт тебе код, перешли его сюда\n'
             'Дальше конвейер сам: ищет CC-видео → бот качает → канал.\n'
             'Telegram не разрешает ботам писать ботам, поэтому ссылку SaveAsBot отправляет обычный аккаунт.')

def bot_api(method, params):
    url = 'https://api.telegram.org/bot%s/%s' % (TOKEN, method)
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode())
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        print('bot_api HTTP', e.code, e.read().decode('utf-8', 'replace')[:300])
        return {'ok': False}

def notify(text):
    bot_api('sendMessage', {'chat_id': OWNER, 'text': text})

def load_pub():
    try:
        return json.load(open(PUB, encoding='utf-8'))
    except Exception:
        return {'ids': {}, 'authors': {}, 'last_topic': None}

def save_pub(p):
    json.dump(p, open(PUB, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def yt_search(topic):
    """YouTube Data API: релевантные CC-видео за 180 дней, сортировка по просмотрам."""
    if not YT_API_KEY:
        return []
    since = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 180 * 86400))
    try:
        q = urllib.parse.quote(topic)
        s = json.load(urllib.request.urlopen(urllib.request.Request(
            'https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=25&type=video'
            '&order=viewCount&relevanceLanguage=ru&videoLicense=creativeCommon&publishedAfter=%s&q=%s&key=%s'
            % (since, q, YT_API_KEY)), timeout=30))
    except Exception as e:
        print('  [api search]', type(e).__name__, str(e)[:100])
        return []
    ids = [i['id']['videoId'] for i in s.get('items', []) if i.get('id', {}).get('videoId')]
    if not ids:
        return []
    try:
        v = json.load(urllib.request.urlopen(urllib.request.Request(
            'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,status,contentDetails&id=%s&key=%s'
            % (','.join(ids), YT_API_KEY)), timeout=30))
    except Exception:
        return []
    out = []
    for it in v.get('items', []):
        if (it.get('status') or {}).get('license') != 'creativeCommon':
            continue
        dur = it.get('contentDetails', {}).get('duration') or 'PT0S'
        m = re.match(r'PT(?:(\d+)M)?(?:(\d+)S)?', dur)
        secs = (int(m.group(1) or 0) * 60 if m else 0) + (int(m.group(2) or 0) if m else 0)
        if secs and secs > 185:
            continue
        out.append({'videoId': it['id'], 'topic': topic,
                    'views': int((it.get('statistics') or {}).get('viewCount') or 0),
                    'title': it.get('snippet', {}).get('title'),
                    'author': it.get('snippet', {}).get('channelTitle'),
                    'url': 'https://www.youtube.com/shorts/' + it['id']})
    return out

def pick_candidates(pub):
    cand, seen = [], set()
    for topic in TOPICS:
        for c in yt_search(topic):
            if c['videoId'] in seen or pub['ids'].get(c['videoId']):
                continue
            seen.add(c['videoId'])
            cand.append(c)
    cand.sort(key=lambda x: -x['views'])
    return cand

def validate_video(path, min_dur=2.0):
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                            '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', path],
                           capture_output=True, text=True, timeout=60)
        dur = float((r.stdout or '0').strip() or 0)
    except Exception:
        dur = 0.0
    return dur >= min_dur, dur

def send_video_file(path, caption):
    boundary = uuid.uuid4().hex
    parts = [('--%s\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n%s\r\n' % (boundary, CHANNEL)).encode(),
             ('--%s\r\nContent-Disposition: form-data; name="caption"\r\n\r\n%s\r\n' % (boundary, caption)).encode(),
             ('--%s\r\nContent-Disposition: form-data; name="supports_streaming"\r\n\r\ntrue\r\n' % boundary).encode(),
             ('--%s\r\nContent-Disposition: form-data; name="video"; filename="%s"\r\nContent-Type: video/mp4\r\n\r\n' % (boundary, os.path.basename(path))).encode(),
             open(path, 'rb').read(),
             ('\r\n--%s--\r\n' % boundary).encode()]
    req = urllib.request.Request('https://api.telegram.org/bot%s/sendVideo' % TOKEN,
        data=b''.join(parts), headers={'Content-Type': 'multipart/form-data; boundary=%s' % boundary})
    try:
        return json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        print('sendVideo HTTP', e.code, e.read().decode('utf-8', 'replace')[:300])
        return {'ok': False}

def caption_for(c):
    tag = '#зарядка' if 'заряд' in c['topic'] else ('#зима' if 'зим' in c['topic'] else '#ev')
    return ('🎬 %s\n\n📺 Автор: %s · лицензия Creative Commons\n%s\n\n%s #видео #запасхода'
            % (c['title'][:80], c['author'], c['url'], tag))

def fetch_via_bot(client, dl_bot, url, sent_marker):
    """Отправляем ссылку боту-скачивалке и ждём файл. Обрабатываем кнопки качества."""
    deadline = time.time() + 300
    clicked = set()
    client.send_message(dl_bot, url)
    while time.time() < deadline:
        time.sleep(10)
        msgs = list(client.iter_messages(dl_bot, limit=6, min_id=sent_marker))
        for m in reversed(msgs):
            if m.video or (m.document and 'video' in (m.document.mime_type or '')):
                return client.download_media(m, '/tmp/fetch_%s.mp4' % re.sub(r'\W', '_', dl_bot))
            if m.buttons and id(m) not in clicked:
                clicked.add(id(m))
                best, best_n = None, -1
                for row in m.buttons:
                    for b in row:
                        mm = re.search(r'(\d{3,4})', b.text or '')
                        n = int(mm.group(1)) if mm else (-1 if b.text and 'mp4' in b.text.lower() else -1)
                        if n > best_n:
                            best_n, best = n, b
                if best is not None:
                    try:
                        best.click()
                        print('  [fetch] кликнул кнопку:', (best.text or '')[:30])
                    except Exception as e:
                        print('  [fetch] click fail:', type(e).__name__)
            elif m.text and time.time() - m.date.timestamp() < 20 and 'больше' in (m.text or '').lower():
                print('  [fetch] бот ответил:', (m.text or '')[:120])
    return None

def main():
    if not (API_ID and API_HASH and SESSION):
        print('нет TG_API_ID/TG_API_HASH/TG_SESSION — шлю инструкцию владельцу')
        notify(SETUP_MSG)
        return
    pub = load_pub()
    cand = pick_candidates(pub)
    print('кандидатов:', len(cand))
    if not cand:
        notify('ℹ️ Новых CC-кандидатов не нашлось в этом прогоне.')
        return
    from telethon.sync import TelegramClient
    from telethon.sessions import StringSession
    posted = False
    dl_bot = '?'
    for c in cand[:3]:
        if c['views'] < MIN_VIEWS:
            break
        path = None
        for dl_bot in DL_BOTS:
            try:
                with TelegramClient(StringSession(SESSION), int(API_ID), API_HASH) as client:
                    sent = client.send_message(dl_bot, c['url'])
                    path = fetch_via_bot(client, dl_bot, c['url'], sent.id)
            except Exception as e:
                print('  [fetch %s]' % dl_bot, type(e).__name__, str(e)[:120])
                path = None
            if path and os.path.exists(path):
                break
        if not path:
            continue
        okv, dur = validate_video(path)
        size = os.path.getsize(path)
        print('  [fetch] файл:', size, 'байт, длительность', dur)
        if not okv or size > MAX_BYTES:
            notify('⚠️ Файл по %s битый/большой (%.1fs, %d байт) — пропустил.' % (c['url'], dur, size))
            continue
        sent = send_video_file(path, caption_for(c))
        print('  [post] ok=', sent.get('ok'), 'msg=', (sent.get('result') or {}).get('message_id'))
        if sent.get('ok'):
            pub['ids'][c['videoId']] = {'title': c['title'], 'author': c['author'],
                                        'views': c['views'], 'topic': c['topic'],
                                        'ts': time.time(), 'src': 'fetcher'}
            pub['last_topic'] = c['topic']
            save_pub(pub)
            notify('✅ Шорт опубликован: «%s» (через @%s)' % (c['title'][:60], dl_bot))
            posted = True
            break
        notify('⚠️ Не смог опубликовать файл по %s: %s' % (c['url'], (sent.get('description') or 'ошибка')[:120]))
    if not posted:
        print('в этом прогоне ничего не опубликовано')

if __name__ == '__main__':
    main()
