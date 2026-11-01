#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collector новостей «Запас хода» — запускается в GitHub Actions (каждые 3 часа).
Собирает свежие EV-новости (Bing News RSS) → чистит → дедуп → скоринг →
пишет статью через LLM-цепочку (llm.py) → сохраняет в data/news/*.json → коммит.
Полный автопостинг в канал НЕ делает: тизеры публикует GAS после подтверждения пользователем.
"""
import os, re, json, html, hashlib, subprocess, sys, datetime, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NEWS_DIR = os.path.join(ROOT, 'data', 'news')
SEEN = os.path.join(ROOT, 'data', 'seen.json')

QUERIES = [
    'электромобиль зарядка Россия', 'запас хода электромобиля зима',
    'батарея электромобиля деградация', 'зарядная станция Россия',
    'Zeekr Россия', 'Li Auto Россия', 'BYD Россия',
    'электромобили в России новости', 'адаптер GB/T', 'CCS2 зарядка',
    'Kia EV Россия', 'электромобиль продажа Россия',
]
KEYWORDS_HI = ['заряд', 'зарядк', 'батарея', 'батаре', 'запас хода', 'электромобиль', 'электромобил',
               'адаптер', 'gb/t', 'ccs', 'winter', 'зим', 'постпродаж', 'гарантия', ' recalled', 'отзыв']
KEYWORDS_BRAND = ['zeekr','li auto','byd','voyah','avatr','hongqi','geely','deepal','xiaomi','xpeng',
                  'tesla','nissan','kia','hyundai','vw','volkswagen','bmw','mercedes','audi','skoda',
                  'evolute','moskvich','aito','changan','exeed','ora','mg ','denza','onvo','icaru','icar','seres']
MAX_ARTICLES_PER_RUN = 3
MAX_PER_DAY = 8

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; zapashoda-bot/1.0; +https://zapashoda.рф)'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def bing_rss(query):
    url = 'https://www.bing.com/news/search?q=' + urllib.parse.quote(query) + '&format=rss&setmkt=ru-RU&setlang=ru'
    try:
        raw = fetch(url)
    except Exception:
        return []
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(raw)
        out = []
        for item in root.iter('item'):
            title = (item.findtext('title') or '').strip()
            link = (item.findtext('link') or '').strip()
            desc = html.unescape(re.sub(r'<[^>]+>', '', item.findtext('description') or '')).strip()
            pub = item.findtext('pubDate') or ''
            out.append({'title': title, 'link': link, 'desc': desc, 'pub': pub})
        return out
    except Exception:
        return []

import urllib.parse  # noqa: E402

def clean_text(s):
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:6000]

def page_text(url):
    """Лёгкий fetch полного текста: без headless-браузера. Crawl4AI подключим в v2."""
    try:
        raw = fetch(url, timeout=20)
        if isinstance(raw, bytes):
            try: raw = raw.decode('utf-8')
            except UnicodeDecodeError: raw = raw.decode('cp1251', 'ignore')
        raw = re.sub(r'(?is)<(script|style|nav|header|footer|aside|form)[^>]*>.*?</\1>', ' ', raw)
        paras = re.findall(r'(?is)<p[^>]*>(.*?)</p>', raw)
        text = ' '.join(re.sub(r'<[^>]+>', '', p) for p in paras)
        text = html.unescape(text)
        return clean_text(text)
    except Exception:
        return ''

def score(item):
    t = (item['title'] + ' ' + item['desc']).lower()
    s = 0
    for kw in KEYWORDS_HI:
        if kw in t: s += 2
    for kw in KEYWORDS_BRAND:
        if kw in t: s += 3
    if len(item['title']) < 25: s -= 2
    if any(x in t for x in ['курс', 'котиров', 'война', 'акци', 'цб рф', 'ставк']): s -= 5
    return s

def slugify(s):
    tr = str.maketrans({'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y',
                        'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f',
                        'х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
                        ' ':'-','/':'-','.':'-','(':'',')':'',',':'','+':'','–':'-','—':'-',':':'','«':'','»':'','"':''})
    s = re.sub(r'-+', '-', re.sub(r'[^a-z0-9\-]', '', s.lower().translate(tr))).strip('-')
    return s[:60] or 'news'

def load_seen():
    if os.path.exists(SEEN):
        with open(SEEN, encoding='utf-8') as f: return json.load(f)
    return {}

def save_seen(seen):
    with open(SEEN, 'w', encoding='utf-8') as f: json.dump(seen, f, ensure_ascii=False, indent=1)

def today_count():
    today = datetime.date.today().isoformat()
    return sum(1 for fn in os.listdir(NEWS_DIR) if fn.startswith(today))

def main():
    seen = load_seen()
    if today_count() >= MAX_PER_DAY:
        print('Дневной лимит достигнут — выход'); return
    sys.path.insert(0, HERE)
    import llm
    all_items = []
    for q in QUERIES:
        all_items.extend(bing_rss(q))
    dedup = []
    for it in all_items:
        key = hashlib.md5(it['link'].encode()).hexdigest()[:16]
        it['hash'] = key
        if key in seen: continue
        dedup.append(it)
    dedup = [it for it in dedup if len(it['title']) > 15]
    dedup.sort(key=lambda x: score(x), reverse=True)
    written = 0
    for it in dedup:
        if written >= MAX_ARTICLES_PER_RUN or today_count() >= MAX_PER_DAY: break
        text = page_text(it['link'])
        src_text = (it['desc'] + ' ' + text).strip()[:4000]
        if len(src_text) < 200:  # слишком мало текста — пропускаем
            continue
        art = llm.write_article(it['title'], src_text, it['link'])
        if not art: continue
        slug = slugify(art.get('title') or it['title'])
        date = datetime.date.today().isoformat()
        fn = os.path.join(NEWS_DIR, f'{date}-{slug}.json')
        if os.path.exists(fn): continue
        art.update({'slug': slug, 'date': date, 'source': it['link']})
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(art, f, ensure_ascii=False, indent=1)
        seen[it['hash']] = {'url': it['link'], 'date': date}
        written += 1
        print('статья:', fn.split('/')[-1])
    save_seen(seen)
    # ограничение seen.json 3000 записей
    if len(seen) > 3000:
        keep = sorted(seen.items(), key=lambda kv: kv[1].get('date',''), reverse=True)[:3000]
        save_seen(dict(keep))
    if written:
        print('новых статей:', written)
        # коммит (в Actions есть permissions: write)
        try:
            subprocess.run(['git', 'config', 'user.email', 'actions@users.noreply.github.com'], cwd=ROOT, check=True)
            subprocess.run(['git', 'config', 'user.name', 'zapashoda-news-bot'], cwd=ROOT, check=True)
            subprocess.run(['git', 'add', 'data'], cwd=ROOT, check=True)
            if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode != 0:
                subprocess.run(['git', 'commit', '-m', 'news: auto-collected ' + datetime.datetime.now().strftime('%d.%m %H:%M')], cwd=ROOT, check=True)
                subprocess.run(['git', 'push'], cwd=ROOT, check=True)
                print('commit+push OK')
        except Exception as e:
            print('git WARN:', e)
    else:
        print('новых статей нет')

if __name__ == '__main__':
    main()
