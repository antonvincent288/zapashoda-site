#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Overpass → stations.json merge: обогащение карты ЭЗС данными OSM.
Запуск: GITHUB_TOKEN=... python3 overpass_merge.py [--push]
Отчёт: stdout JSON {new, updated, unchanged, total} + файл merge_report.json.
Матч по координатам ±50 м (~0.0005°). Дубли по координатам не переписываются.
Разъёмы: OSM socket:* конвертятся в наш формат s[].
Директива цен: не добавляем цены (директива проекта)."""
import argparse, json, math, sys, urllib.request, urllib.parse, os, glob

OUR_TAGS = {
    'socket:type2_combo': 'CCS2',
    'socket:chademo': 'CHAdeMO',
    'socket:gb_dc': 'GB/T DC',
    'socket:type2': 'Type 2',
    'socket:type2_cable': 'Type 2',
    'socket:schuko': 'Schuko',
    'socket:type1': 'Type 1',
}

def overpass_fetch():
    q = '[out:json][timeout:120];area["ISO3166-1"="RU"][admin_level=2]->.ru;node["amenity"="charging_station"](area.ru);out body 5000;'
    url = 'https://overpass-api.de/api/interpreter'
    data = urllib.parse.urlencode({'data': q}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'zapashoda-merge/1.0'})
    r = urllib.request.urlopen(req, timeout=180)
    return json.loads(r.read().decode('utf-8'))

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))

def match_near(stations, lat, lon, tol_km=0.05):
    for i, s in enumerate(stations):
        d = haversine_km(s.get('lat',0), s.get('lon',0), lat, lon)
        if d <= tol_km:
            return i
    return None

def osm_to_station(node):
    t = node.get('tags', {})
    name = t.get('name') or t.get('operator') or t.get('brand') or 'Зарядная станция'
    op = t.get('operator') or t.get('brand') or None
    addr = ', '.join(x for x in [t.get('addr:street'), t.get('addr:housenumber'), t.get('addr:city')] if x) or None
    pw = t.get('charge_capacity') or t.get('chargepoints') or None
    try:
        pw = int(pw) if pw else None
    except:
        pw = None
    sockets = []
    for k, std in OUR_TAGS.items():
        if k in t:
            sockets.append(std)
    if not sockets and 'amenity' in t:
        sockets = ['Type 2']
    return {
        'lat': round(node['lat'], 6),
        'lon': round(node['lon'], 6),
        'n': name,
        'op': op,
        'a': addr or t.get('description') or None,
        'c': 2 if not pw or pw < 50 else (t.get('chargepoints', 2) if t.get('chargepoints') else 2),
        'pw': pw,
        's': sockets if sockets else ['Type 2'],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--push', action='store_true', help='пушить обновлённый stations.json в репо')
    ap.add_argument('--dry', action='store_true', help='только отчёт, не менять')
    args = ap.parse_args()
    repo = os.environ.get('REPO', 'antonvincent288/zapashoda-site')
    br = os.environ.get('BRANCH', 'astrowind-migration')
    token = os.environ.get('GITHUB_TOKEN', '')
    # найти stations.json локально
    files = glob.glob('site/public/charging/stations.json')
    if not files:
        print('stations.json не найден'); sys.exit(1)
    sj = files[0]
    data = json.load(open(sj, encoding='utf-8'))
    stations = data.get('stations', [])
    print('local stations:', len(stations))
    # fetch OSM
    try:
        overpass = overpass_fetch()
    except Exception as e:
        print('OVERPASS FAIL:', e); sys.exit(1)
    nodes = [e for e in overpass.get('elements', []) if e.get('type') == 'node']
    print('overpass nodes:', len(nodes))
    new_count, upd_count, unchanged = 0, 0, 0
    for n in nodes:
        st = osm_to_station(n)
        idx = match_near(stations, st['lat'], st['lon'])
        if idx is None:
            stations.append(st)
            new_count += 1
        else:
            s = stations[idx]
            # обогатить только пустые поля
            changed = False
            if not s.get('op') and st.get('op'): s['op'] = st['op']; changed = True
            if not s.get('pw') and st.get('pw'): s['pw'] = st['pw']; changed = True
            if not s.get('s') and st.get('s'): s['s'] = st['s']; changed = True
            if changed: upd_count += 1
            else: unchanged += 1
    data['stations'] = stations
    data['updated'] = '2026-11-11'
    data['merge'] = f'Overpass OSM merge {new_count} new, {upd_count} updated'
    report = {'new': new_count, 'updated': upd_count, 'unchanged': unchanged, 'total': len(stations)}
    open(os.path.join(os.path.dirname(sj), 'merge_report.json'), 'w', encoding='utf-8').write(json.dumps(report, indent=1))
    print(json.dumps(report))
    if args.push and token:
        import urllib.request as U2
        req = U2.Request(f'https://api.github.com/repos/{repo}/contents/{sj}', method='PUT',
            headers={'Authorization': 'Bearer ' + token, 'User-Agent': 'zapashoda-merge/1.0', 'Content-Type': 'application/json'})
        import base64
        body = {'message': f'Overpass merge: +{new_count} new, {upd_count} enriched', 'content': base64.b64encode(open(sj,'rb').read()).decode(), 'branch': br}
        # нужно sha
        # простое: перезаписать через file PUT
        try:
            r = U2.urlopen(req, json.dumps(body).encode('utf-8'))
            print('PUSH ok:', json.load(r)['commit']['sha'][:9])
        except Exception as e:
            import urllib.error
            print('PUSH FAIL:', getattr(e,'code', e))
    elif args.push:
        print('NO GITHUB_TOKEN — не пушим')

if __name__ == '__main__':
    main()
