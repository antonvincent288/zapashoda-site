#!/usr/bin/env python3
"""Волна 1.7 GAS/MARGIN-WATCH: standby-мониторинг.

1. Проверяет наличие секрета GAS_CLASP_TOKEN в репозитории (список имён секретов
   доступен через API при правах admin:repo у токена запуска).
2. Проверяет data/product_margins_v1.csv: заполнены ли себестоимости (колонка 4).
Статус — в bridge/gas_watch.json. При появлении токена пишет флаг live_ready=true
(переключение в live делает владелец/архитектор запуском деплоя GAS; Алиса
подтверждает в мосту). Идempотентно, не меняет ничего без вводных.
"""
import json, os, csv, urllib.request
from datetime import datetime, timezone

REPO = os.environ.get('GITHUB_REPOSITORY', 'antonvincent288/zapashoda-site')
API = 'https://api.github.com/repos/%s/actions/secrets' % REPO

def main():
    out = {'ts': datetime.now(timezone.utc).isoformat(), 'clasp_token': False, 'margins_filled': False, 'ready': False}
    tok = os.environ.get('GITHUB_TOKEN', '')
    if tok:
        req = urllib.request.Request(API, headers={'Authorization': 'token ' + tok, 'User-Agent': 'zapashoda-gas-watch'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            names = [s['name'] for s in d.get('secrets', [])]
            out['clasp_token'] = 'GAS_CLASP_TOKEN' in names
            out['secrets_seen'] = names
        except Exception as e:
            out['secret_api_error'] = repr(e)[:120]
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'product_margins_v1.csv')
    if os.path.isfile(csv_path):
        filled = 0
        try:
            with open(csv_path, encoding='utf-8') as f:
                rows = list(csv.reader(f, delimiter=';'))
            for row in rows[1:]:
                if len(row) >= 4 and row[3].strip().replace(',', '').isdigit():
                    filled += 1
            out['margins_filled'] = filled >= len(rows) - 1 and filled > 0
            out['margins_filled_count'] = filled
        except Exception as e:
            out['csv_error'] = repr(e)[:120]
    out['ready'] = out['clasp_token'] and out['margins_filled']
    os.makedirs('bridge', exist_ok=True)
    json.dump(out, open('bridge/gas_watch.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('GAS-WATCH:', 'token=' + str(out['clasp_token']), 'margins=' + str(out['margins_filled']), 'ready=' + str(out['ready']))
    if out['ready']:
        print('::warning::GAS_CLASP_TOKEN и маржи на месте — можно включать live (dry_run=false)')

if __name__ == '__main__':
    main()
