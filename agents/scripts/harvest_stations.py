#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Харвест ЭЗС: Яндекс.Карты SSR (до 25 POI на город) + обогащение из OSM Overpass.
Обновляет site/public/charging/stations.json и static/charging/stations.json.
Только stdlib. Запускается вручную или по cron (.github/workflows/update-stations.yml).
"""
import json, re, time, random, math, collections, os, sys, base64
import urllib.request as U
import urllib.parse as UP
import urllib.error as UE

UA = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"), ("Accept-Language", "ru,en;q=0.9")]
OPENER = U.build_opener(); OPENER.addheaders = UA

CITIES = [(213,'moscow'),(2,'saint-petersburg'),(43,'kazan'),(54,'ekaterinburg'),(65,'novosibirsk'),(47,'nizhny-novgorod'),(56,'chelyabinsk'),(51,'samara'),(39,'rostov-na-donu'),(35,'krasnodar'),(239,'sochi'),(193,'voronezh'),(50,'perm'),(172,'ufa'),(38,'volgograd'),(55,'tyumen'),(62,'krasnoyarsk'),(63,'irkutsk'),(75,'vladivostok'),(76,'khabarovsk'),(16,'yaroslavl'),(15,'tula'),(14,'tver'),(11,'ryazan'),(6,'kaluga'),(12,'smolensk'),(9,'lipetsk'),(8,'kursk'),(4,'belgorod'),(48,'orenburg'),(49,'penza'),(195,'ulyanovsk'),(44,'izhevsk'),(236,'naberezhnye-chelny'),(240,'tolyatti'),(1107,'anapa'),(970,'novorossiysk'),(36,'stavropol'),(11067,'pyatigorsk'),(146,'simferopol'),(959,'sevastopol'),(80,'yuzhno-sakhalinsk'),(64,'kemerovo'),(67,'tomsk'),(197,'barnaul'),(973,'surgut'),(11168,'nizhny-tagil'),(235,'magnitogorsk'),(22,'kaliningrad'),(5,'ivanovo'),(192,'vladimir'),(237,'novokuznetsk'),(10758,'khimki'),(10740,'mytishchi'),(10716,'balashikha'),(10747,'podolsk'),(10738,'lyubertsy'),(10735,'krasnogorsk'),(214,'dolgoprudny'),(10743,'odintsovo'),(20728,'korolev'),(10752,'sergiev-posad'),(10765,'shchyolkovo'),(10725,'domodedovo'),(20571,'zhukovsky'),(21621,'reutov'),(10750,'ramenskoye'),(20523,'elektrostal'),(10754,'serpukhov'),(215,'dubna'),(10734,'kolomna'),(11147,'engels'),(68,'chita'),(74,'yakutsk'),(10752,'sergiev-posad'),(6,'kaluga'),(967,'obninsk')]

KW = ['заряд','заправ','electro','charge','punkt','пункт','энергия москвы','мосэнергосбыт','мосэнерго','мособлэнерго','россети','русгидро','sitronics','электропойнт']
HEUR = {'Type 2','ccs2','chademo'}
OPS = [('Энергия Москвы','энергия москвы'),('Мосэнергосбыт','мосэнергосбыт'),('Мосэнерго','мосэнерго'),('Мособлэнерго','мособлэнерго'),('Россети','россети'),('РусГидро','русгидро'),('Sitronics Electro','sitronics'),('Электропойнт','электропойнт'),('Punkt E','punkt'),('Electro.Cars','electro'),('Яндекс Заправки','яндекс заправки')]

def extract_obj(s, i):
    depth = 0; j = i
    while j < len(s):
        c = s[j]
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return s[i:j+1]
        j += 1
    return None

def harvest_city(gid, slug):
    url = f'https://yandex.ru/maps/{gid}/{slug}/search/{UP.quote("электрозаправка")}/'
    try:
        html = OPENER.open(url, timeout=40).read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f'  [{slug}] fetch error: {e}', flush=True); return []
    items = []; i = 0
    while True:
        i = html.find('{"type":"business"', i + 1)
        if i < 0: break
        raw = extract_obj(html, i)
        if not raw: continue
        try:
            d = json.loads(raw)
            if 'coordinates' in d and d.get('title'):
                items.append({'title': d['title'], 'address': d.get('address', ''), 'coords': d['coordinates']})
        except Exception: pass
    return items

def is_ev(*texts):
    s = ' '.join(texts).lower()
    return any(k in s for k in KW)

def key(lat, lon): return f'{round(lat,4)}|{round(lon,4)}'

def detect_conn(n):
    s = (n or '').lower()
    if any(k in s for k in ['быстр','fast',' dc','dc-','150','120','100']): return ['ccs2','chademo']
    return ['Type 2']

def op_from(n):
    s = (n or '').lower()
    for o, alias in OPS:
        if alias in s: return o
    return None

def osm_nodes():
    q = '[out:json][timeout:180];area["ISO3166-1"="RU"][admin_level=2]->.a;node(area.a)["amenity"="charging_station"];out body 20000;'
    data = UP.urlencode({'data': q}).encode()
    for attempt in range(3):
        try:
            req = U.Request('https://overpass-api.de/api/interpreter', data=data, headers={'User-Agent':'zapashoda-ev/1.0'})
            return json.load(U.urlopen(req, timeout=300)).get('elements', [])
        except Exception as e:
            print(f'  overpass attempt {attempt}: {e}', flush=True); time.sleep(10)
    return []

def max_kw(t):
    vals = []
    for k in ['socket:type2_combo:output','socket:gb_dc:output','socket:chademo:output','socket:type2:output','socket:type2_cable:output','socket:type1:output','socket:gb_ac:output','socket:schuko:output','maxpower','max_power']:
        v = t.get(k)
        if v:
            try: vals.append(float(str(v).replace(',','.').replace(' kW','').replace('кВт','').strip()))
            except Exception: pass
    return max(vals) if vals else None

def norm_conn(t):
    out = []
    for src, tag in [('type2_combo','socket:type2_combo'),('chademo','socket:chademo'),('gb_dc','socket:gb_dc'),('type2','socket:type2'),('type2_cable','socket:type2_cable'),('schuko','socket:schuko'),('type1','socket:type1'),('gb_ac','socket:gb_ac')]:
        if t.get(tag): out.append(src)
    return out

def main():
    repo = 'site/public/charging/stations.json'
    if not os.path.exists(repo): repo = 'charging/stations.json'
    with open(repo, encoding='utf-8') as f:
        data = json.load(f)
    stations = data['stations']
    cur_keys = {key(s['lat'], s['lon']) for s in stations}
    raw = ev = added = 0
    for gid, slug in CITIES:
        its = harvest_city(gid, slug); raw += len(its)
        for it in its:
            if not is_ev(it.get('title',''), it.get('address','')): continue
            ev += 1
            lon, lat = it['coords'][0], it['coords'][1]
            k = key(lat, lon)
            if k in cur_keys: continue
            cur_keys.add(k)
            stations.append({'lat': round(lat,6), 'lon': round(lon,6), 'n': it['title'][:80],
                             'op': op_from(it['title']), 'a': re.sub(r'\s+',' ',it.get('address','')).strip()[:120],
                             'c': len(detect_conn(it['title'])), 'pw': None,
                             's': detect_conn(it['title']), 'src': 'yandex'})
            added += 1
        time.sleep(1.4 + random.random()*0.8)
    print(f'harvest: {len(CITIES)} cities, {raw} raw, {added} added', flush=True)
    # OSM-обогащение
    osm = osm_nodes()
    idx = collections.defaultdict(list)
    for e in osm:
        if e.get('lat') is None: continue
        idx[key(e['lat'], e['lon'])].append(e)
    enriched = 0
    for s in stations:
        cands = idx.get(key(s['lat'], s['lon']), [])
        if not cands: continue
        best = min(cands, key=lambda e:(abs(e['lat']-s['lat'])+abs(e['lon']-s['lon'])))
        dist = math.hypot((best['lat']-s['lat'])*111, (best['lon']-s['lon'])*111*math.cos(math.radians(s['lat'])))
        if dist > 0.15: continue
        t = best.get('tags', {})
        conns = norm_conn(t)
        if conns and set(map(str.lower, s.get('s') or [])) <= HEUR:
            s['s'] = conns; s['c'] = len(conns); enriched += 1
            if s.get('src') == 'yandex': s['src'] = 'yandex+osm'
        kw = max_kw(t)
        if kw and not s.get('pw'): s['pw'] = int(kw)
        op = t.get('operator') or t.get('operator:ru')
        if op and not s.get('op'): s['op'] = op
    print(f'enriched: {enriched}', flush=True)
    data['stations'] = stations
    data['updated'] = time.strftime('%Y-%m-%d')
    for path in ['site/public/charging/stations.json', 'static/charging/stations.json']:
        if os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
    print('total stations:', len(stations), flush=True)

if __name__ == '__main__':
    main()
