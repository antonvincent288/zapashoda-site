#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Смок-прод zapashoda-ev.ru. Уровень 1, только HTTP (без браузера).
Проверяет: HTTP 200, <title>, canonical, og:title+og:image, h1, html lang.
Плюс: sitemap.xml — число URL, отсутствие внешних доменов; robots.txt — маркеры AEO.
Вывод: JSON-отчёт; exit 1 если есть FAIL (кроме .xml/.txt, для них только статус).
Использование:
  python3 smoke_prod.py --urls agents/urls_core.txt --base https://zapashoda-ev.ru/ [--threads 8]
"""
import argparse, json, re, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (compatible; zapashoda-smoke/1.0)"}

def get(url, timeout=45):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
        return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return -1, str(e)[:120]

def check(base, path):
    url = base.rstrip("/") + ("/" + path.lstrip("/") if path else "")
    st, h = get(url)
    res = {"path": path or "/", "status": st}
    if h and not path.endswith((".xml", ".txt")):
        res["title"] = bool(re.search(r"<title>[^<]{5,}</title>", h))
        res["canonical"] = bool(re.search(r'<link[^>]*rel="canonical"', h))
        res["og"] = ("og:title" in h) and ("og:image" in h)
        res["h1"] = bool(re.search(r"<h1", h))
        res["lang"] = bool(re.search(r'<html[^>]*lang="', h))
        if st == 200 and not (res["title"] and res["canonical"]):
            res["verdict"] = "FAIL"
        else:
            res["verdict"] = "ok"
    else:
        res["verdict"] = "ok" if st == 200 else "FAIL"
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", default=None, help="файл со списком путей (по одному в строке)")
    ap.add_argument("--base", default="https://zapashoda-ev.ru/")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--sample-models", type=int, default=8)
    ap.add_argument("--sample-articles", type=int, default=8)
    args = ap.parse_args()
    paths = []
    if args.urls:
        paths = [l.strip() for l in open(args.urls, encoding="utf-8") if l.strip() and not l.startswith("#")]
    else:
        # авто-выборка из локальных данных, если запущено из корня репо
        import glob, os, random
        models = [os.path.basename(f)[:-5] for f in glob.glob("site/src/data/models/*.json")]
        arts = [os.path.basename(f)[:-5] for f in glob.glob("site/src/data/articles/*/*.json")]
        random.seed(11)
        paths = ["", "models/", "catalog/", "calculators/cost/", "calculators/time/", "blog/", "pain/", "services/",
                 "sitemap.xml", "robots.txt"]
        paths += ["models/" + s + "/" for s in random.sample(models, min(args.sample_models, len(models)))]
        paths += ["blog/" + os.path.splitext(os.path.basename(a))[0] + "/" for a in random.sample(arts, min(args.sample_articles, len(arts)))]
    with ThreadPoolExecutor(args.threads) as ex:
        results = list(ex.map(lambda p: check(args.base, p), paths))
    st, sm = get(args.base.rstrip("/") + "/sitemap.xml")
    sitemap_urls = len(re.findall(r"<loc>", sm)) if st == 200 else -1
    st_r, rob = get(args.base.rstrip("/") + "/robots.txt")
    aeo = ("GPTBot" in rob) and ("PerplexityBot" in rob) if st_r == 200 else False
    report = {
        "base": args.base, "checked": len(results),
        "fail": [r for r in results if r["verdict"] == "FAIL"],
        "sitemap_urls": sitemap_urls, "robots_aeo": aeo,
        "status": "PASS" if all(r["verdict"] == "ok" for r in results) and sitemap_urls > 0 and aeo else "FAIL",
    }
    out = json.dumps(report, ensure_ascii=False, indent=1)
    print(out[:6000])
    sys.exit(1 if report["status"] == "FAIL" else 0)

if __name__ == "__main__":
    main()
