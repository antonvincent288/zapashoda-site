#!/usr/bin/env python3
"""R-06: приёмник шортов от Арт-Директора.

Ищет файлы assets/shorts/incoming/*.mp4 (+ необязательный .json с title/desc рядом).
Каждый файл: ffmpeg приводит к вертикали 1080x1920, режет до 30 сек,
накладывает верхнюю плашку «ЗАПАС ХОДА» (VISUAL_SPEC: антрацит + золото),
кладёт готовый ролик в assets/shorts/published/, пишет запись в
scripts/shorts_published.json и data/shorts.json (страница /shorts/ и
video-sitemap.xml собираются из неё при следующей сборке). Публикация в ТГ.
"""
import json, os, subprocess, glob, sys, datetime, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, '..', 'assets', 'shorts', 'incoming')
OUT = os.path.join(HERE, '..', 'assets', 'shorts', 'published')
PUB = os.path.join(HERE, 'shorts_published.json')
TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
CHANNEL = os.environ.get('CHANNEL_ID', '-1002316192115')

def ffmpeg_available():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=30)
        return True
    except Exception:
        return False

def publish_tg(path, caption, url_hint=None):
    if not TOKEN:
        print('no TELEGRAM_TOKEN — только локальная публикация'); return
    cap = caption if url_hint is None else (caption + '\n\n' + url_hint)
    # multipart не нужен: sendVideo требует multipart — упрощённо шлём как документ через FormData минимально
    boundary = 'zs' + str(id(path))
    with open(path, 'rb') as f:
        data = f.read()
    body = []
    body.append(('--%s\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n%s\r\n' % (boundary, CHANNEL)).encode())
    body.append(('--%s\r\nContent-Disposition: form-data; name="caption"\r\n\r\n%s\r\n' % (boundary, cap)).encode())
    body.append(('--%s\r\nContent-Disposition: form-data; name="video"; filename="%s"\r\nContent-Type: video/mp4\r\n\r\n' % (boundary, os.path.basename(path))).encode())
    body.append(data)
    body.append(('--%s--\r\n' % boundary).encode())
    req = urllib.request.Request('https://api.telegram.org/bot%s/sendVideo' % TOKEN,
        data=b''.join(body), headers={'Content-Type': 'multipart/form-data; boundary=%s' % boundary})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            res = json.load(r)
            print('TG:', res.get('ok'))
    except Exception as e:
        print('TG fail:', repr(e)[:160])

def main():
    if not os.path.isdir(IN):
        os.makedirs(IN, exist_ok=True)
    files = sorted(glob.glob(os.path.join(IN, '*.mp4')))[:1]  # один шорт за прогон — не спамим канал
    if not files:
        print('нет входящих видео — ок'); return
    if not ffmpeg_available():
        print('ffmpeg не найден'); sys.exit(1)
    os.makedirs(OUT, exist_ok=True)
    pub = json.load(open(PUB, encoding='utf-8')) if os.path.exists(PUB) else {'items': []}
    have = {it['file'] for it in pub['items']}
    records = []
    caps = []
    for f in files:
        base = os.path.splitext(os.path.basename(f))[0]
        meta_f = os.path.splitext(f)[0] + '.json'
        title, desc, tags, no_plate = base, 'Шорт «Запас хода»', [], False
        if os.path.exists(meta_f):
            try:
                meta = json.load(open(meta_f, encoding='utf-8'))
                title = meta.get('title') or title
                desc = meta.get('desc') or desc
                tags = meta.get('tags') or []
                no_plate = bool(meta.get('no_plate'))
            except Exception: pass
        cap = title + '\n\n' + (desc + '\n' if desc else '')
        cap += ' '.join(tags + ['#видео', '#запасхода'])
        outname = base + '_zs30.mp4'
        outpath = os.path.join(OUT, outname)
        if no_plate:
            vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        else:
            vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                  "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='ЗАПАС ХОДА':fontcolor=#D4AF37:fontsize=58:borderw=4:bordercolor=#1d1d1f:x=(w-text_w)/2:y=120,"
                  "drawbox=x=0:y=0:w=1080:h=90:color=#1d1d1f@0.85:t=fill")
        cmd = ['ffmpeg', '-y', '-i', f, '-t', '30', '-vf', vf,
               '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-c:a', 'aac', '-b:a', '128k', outpath]
        print('processing', base)
        r = subprocess.run(cmd, capture_output=True, timeout=900)
        if r.returncode != 0:
            print('ffmpeg fail:', r.stderr.decode()[-400:]); continue
        rec = {'file': outname, 'title': title, 'desc': desc, 'tags': tags,
               'url': '/assets/shorts/published/' + outname,
               'added': os.environ.get('BUILD_DATE') or datetime.date.today().isoformat(),
               'kind': 'synthetic' if no_plate else 'ingest', 'script_id': base}
        if outname not in have:
            pub['items'].append(rec)
            have.add(outname)
        records.append(rec)
        caps.append(cap)
        try: os.remove(f)  # входящий файл обработан
        except Exception: pass
    json.dump(pub, open(PUB, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # data/shorts.json для сборки
    data_dir = os.path.join(HERE, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    json.dump({'updated': pub.get('items') and pub['items'][-1].get('added') or '',
               'shorts': pub['items'][-12:]},
              open(os.path.join(data_dir, 'shorts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for rec, cap in zip(records, caps):
        publish_tg(os.path.join(OUT, rec['file']), cap,
                   'Полные гайды: https://zapashoda-ev.ru/shop/digital/')
    print('done:', len(records), 'processed')

if __name__ == '__main__':
    main()
