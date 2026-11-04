#!/usr/bin/env python3
"""R-00 SEO-Спайдер: обход sitemap прод-сайта, проверка доступности, статус в bridge/seo_spider.json.

Логика: читает https://zapashoda-ev.ru/sitemap.xml, HEAD-проверяет каждый URL
(лимит 700), считает долю 200. Итог — файл bridge/seo_spider.json (ts, checked,
ok, pct, fails). Если pct < 95 — пишет отдельный флаг alert в тот же файл
(обход триггерится шагом turbo.yml и консольным сообщением).
"""
import json, os, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

SITE = "https://zapashoda-ev.ru"
LIMIT = 700

def head_ok(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "zapashoda-seo-spider"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status == 200
    except Exception:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "zapashoda-seo-spider"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.status == 200
        except Exception:
            return False

def main():
    urls = []
    try:
        with urllib.request.urlopen(SITE + "/sitemap.xml", timeout=30) as r:
            raw = r.read()
        root = ET.fromstring(raw)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [el.text for el in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    except Exception as e:
        print("sitemap read failed:", repr(e)[:120])
        urls = []
    urls = [u.strip() for u in urls if u.startswith("http")][:LIMIT]
    ok = 0
    fails = []
    for i, u in enumerate(urls):
        if head_ok(u):
            ok += 1
        else:
            fails.append(u)
        if i % 40 == 0:
            print("progress", i, "/", len(urls))
    checked = len(urls)
    pct = round(100.0 * ok / checked, 1) if checked else 0.0
    res = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "checked": checked,
        "ok": ok,
        "pct": pct,
        "alert": pct < 95.0,
        "fails": fails[:30],
    }
    os.makedirs("bridge", exist_ok=True)
    json.dump(res, open("bridge/seo_spider.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("SEO-Spider:", checked, "URL,", ok, "OK,", pct, "%", ("ALERT" if res["alert"] else ""))
    if res["alert"]:
        print("::warning::индексация ниже 95% — нужен переобход")

if __name__ == "__main__":
    main()
