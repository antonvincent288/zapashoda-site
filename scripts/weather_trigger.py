#!/usr/bin/env python3
# R-09 «Зимний кластер»: монитор температуры (Москва/Химки, open-meteo).
# Если мин. температура в ближайшие 3 дня <= -10 C — bridge/winter_seo.json: triggered=true,
# и build_sitemap повышает приоритет зимних статей до 0.9 на 48 часов.
import json, os, time, urllib.request

LAT, LON = 55.8894, 37.4449
WINTER_ARTICLES = ['blog/winter-ev-2026.html', 'blog/kvt-i-kvt-ch-raznica.html',
                   'blog/rasxod-zimoy-bortovoy-kompyuter.html', 'routes/', 'calculator/']

def main():
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
           "&daily=temperature_2m_min&forecast_days=3&timezone=Europe/Moscow")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read())
        tmins = data.get('daily', {}).get('temperature_2m_min') or []
        tmin = min(tmins) if tmins else None
    except Exception as e:
        print('weather fetch failed:', e); tmin = None
    triggered = tmin is not None and tmin <= -10
    status = {
        'updated': time.strftime('%Y-%m-%dT%H:%M:%S+03:00'),
        'source': 'open-meteo daily temp_min, 3 days',
        'temp_min': tmin,
        'triggered': triggered,
        'winter_articles': WINTER_ARTICLES if triggered else [],
        'priority': '0.9 (48h)' if triggered else 'default'
    }
    os.makedirs('bridge', exist_ok=True)
    with open('bridge/winter_seo.json', 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    print(json.dumps(status, ensure_ascii=False))

if __name__ == '__main__':
    main()
