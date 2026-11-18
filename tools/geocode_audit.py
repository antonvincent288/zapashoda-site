#!/usr/bin/env python3
# Фоновая сверка координат ЭЗС с адресами (zapashoda-ev.ru).
# Для каждой точки stations.json геокодируем адрес (Nominatim -> Photon fallback),
# сравниваем расстояние. Смещения >300 м при совпадении улицы — правим координату,
# прочие крупные расхождения — только помечаем в отчёте geo_audit.json.
import json, math, os, re, time, urllib.request, urllib.parse
from datetime import datetime, timezone

BRANCH = os.environ.get('AUDIT_BRANCH', 'astrowind-migration')
BASE = 'https://raw.githubusercontent.com/antonvincent288/zapashoda-site/%s/' % BRANCH
UA = 'zapashoda-geocode-audit/1.0 (https://zapashoda-ev.ru)'
STREET_STOP = {'улица','ул','проспект','пр','шоссе','дорога','бульвар','набережная','проезд','переулок','пер','площадь','пл','территория','тер','город','г'}

def get(url, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def geocode_nominatim(q):
    u = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({'q': q, 'format': 'jsonv2', 'limit': 1})
    try:
        arr = json.loads(get(u))
        if arr:
            return float(arr[0]['lat']), float(arr[0]['lon']), arr[0].get('type',''), arr[0].get('display_name','')
    except Exception:
        return None
    return None

def geocode_photon(q):
    u = 'https://photon.komoot.io/api/?' + urllib.parse.urlencode({'q': q, 'limit': 1})
    try:
        d = json.loads(get(u))
        f = (d.get('features') or [None])[0]
        if f:
            c = f['geometry']['coordinates']
            pr = f.get('properties', {})
            disp = ' '.join(str(v) for v in [pr.get('name'), pr.get('street'), pr.get('city'), pr.get('state')] if v)
            return float(c[1]), float(c[0]), pr.get('osm_value',''), disp
    except Exception:
        return None
    return None

def haversine(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    dlat, dlon = lat2-lat1, lon2-lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000 * 2 * math.asin(math.sqrt(h))

def norm(s):
    return re.sub(r'[^\wа-яё ]', ' ', (s or '').lower(), flags=re.UNICODE)

def overlap(addr, disp):
    toks = [t for t in norm(addr).split() if len(t) > 3 and t not in STREET_STOP and not t.isdigit()]
    if not toks:
        return False
    dn = norm(disp)
    return sum(1 for t in toks if t in dn) >= min(2, len(toks))

def is_real_address(addr):
    low = addr.lower()
    street = re.search(r'(?:ул|улица|проспект|пр-т|шоссе|бульвар|наб|проезд|переулок|площадь|тер|линия|дорога|тракт|аллея|тупик|просп)', low)
    return bool(street) or (bool(re.search(r'\d', addr)) and ',' in addr)

def main():
    data = json.loads(get(BASE + 'site/public/charging/stations.json'))
    stations = data.get('stations', [])
    report = {'updated': None, 'total': len(stations), 'offset': offset, 'batch_end': end, 'checked': 0, 'fixed': 0, 'flagged': 0,
              'non_address': 0, 'geocoder_blocked': False, 'fixes': [], 'flagged_items': []}
    limit = int(os.environ.get('AUDIT_LIMIT', '0') or 0)
    offset = int(os.environ.get('AUDIT_OFFSET', '0') or 0)
    start = offset
    end = min(len(stations), start + limit) if limit else len(stations)
    snap_usage = {}
    staged = []
    for i in range(start, end):
        x = stations[i]
        addr = (x.get('a') or '').strip()
        if not addr or addr == 'Адрес не указан':
            report['non_address'] += 1
            continue
        if not is_real_address(addr):
            report['non_address'] += 1
            continue
        res = geocode_nominatim(addr) or geocode_photon(addr)
        if res is None:
            report['geocoder_blocked'] = True
            time.sleep(2.0)
            continue
        lat, lon, typ, disp = res
        d = haversine((x['lat'], x['lon']), (lat, lon))
        report['checked'] += 1
        if d > 300:
            item = {'i': i, 'n': (x.get('n') or '')[:60], 'a': addr[:120], 'old': [x['lat'], x['lon']], 'new': [round(lat,6), round(lon,6)], 'd_m': int(d), 'type': typ}
            nums = set(re.findall(r'(?<!\d)(\d{1,4})(?!\d)', addr))
            dn = norm(disp)
            house_ok = any(nn in dn for nn in nums) if nums else False
            city_ok = overlap(addr, disp)
            key = (round(lat,4), round(lon,4))
            if d < 50000 and house_ok and city_ok and snap_usage.get(key, 0) < 3:
                staged.append((i, x, item, key))
            elif d > 800:
                report['flagged'] += 1
                if len(report['flagged_items']) < 300:
                    report['flagged_items'].append(item)
        time.sleep(1.1)
    for i, x, item, key in staged:
        if snap_usage.get(key, 0) >= 3:
            report['flagged'] += 1
            if len(report['flagged_items']) < 300:
                report['flagged_items'].append(item)
            continue
        x['lat'], x['lon'] = item['new'][0], item['new'][1]
        snap_usage[key] = snap_usage.get(key, 0) + 1
        report['fixed'] += 1
        report['fixes'].append(item)
    report['updated'] = datetime.now(timezone.utc).isoformat()
    json.dump(report, open('geo_audit.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(data, open('stations_fixed.json', 'w'), ensure_ascii=False)
    print('checked=%d fixed=%d flagged=%d non_address=%d blocked=%s' % (report['checked'], report['fixed'], report['flagged'], report['non_address'], report['geocoder_blocked']))

main()
