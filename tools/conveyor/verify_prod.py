#!/usr/bin/env python3
"""Conveyor helper: production verification with CDN-cache retry.

Usage: python tools/conveyor/verify_prod.py --slug my-slug --badge 11.11.2026 --probe "фраза 1" --probe "фраза 2"
Prints JSON report. Exit 0 on success.
"""
import argparse, json, sys, time, urllib.request, urllib.error

def get(url, timeout=30):
    r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Chrome/124'})
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, b''
    except Exception:
        return 0, b''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slug', required=True)
    ap.add_argument('--badge', required=True, help='Актуально: DD.MM.YYYY')
    ap.add_argument('--probe', action='append', default=[])
    ap.add_argument('--max-tries', type=int, default=10)
    ap.add_argument('--sleep', type=int, default=95)
    a = ap.parse_args()
    report = {'slug': a.slug, 'attempts': 0, 'ok': False, 'probes': {}}
    for attempt in range(a.max_tries):
        time.sleep(a.sleep)
        st, h = get(f'https://zapashoda-ev.ru/blog/{a.slug}/?r={attempt}')
        badge_ok = f'Актуально: {a.badge}'.encode('utf-8') in h
        faq = b'FAQPage' in h
        report['attempts'] += 1
        print(f'{attempt}: page {st}, FAQ={faq}, badge={badge_ok}', file=sys.stderr)
        if st == 200 and faq and badge_ok:
            for p in a.probe:
                report['probes'][p] = p.encode('utf-8') in h
            st_og, _ = get(f'https://zapashoda-ev.ru/assets/og/b-{a.slug}.png?r=1')
            report['ok'] = all(report['probes'].values()) and st_og == 200
            report['og'] = st_og
            break
    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0 if report['ok'] else 1)

if __name__ == '__main__':
    main()
