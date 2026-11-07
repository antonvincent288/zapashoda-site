#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync прод-данных (main) в Astro-дерево (astrowind-migration checkout).

Новые слаги data/blog_extra/*.json -> astro/site/src/data/articles/blog/{slug}.json
og-плашки main/assets/og/b-*.png   -> astro/site/public/assets/og/

Правило: существующие миграционные статьи НЕ перезаписываются (там вычищенная
вёрстка), добавляются только новые слаги прод-конвейера. Запускается шагом
деплоя перед сборкой Astro.
"""
import json, os, glob, datetime, shutil

MAIN = "main"
ASTRO = "astro"
ARTDIR = os.path.join(ASTRO, "site", "src", "data", "articles", "blog")
OGDIR = os.path.join(ASTRO, "site", "public", "assets", "og")
os.makedirs(ARTDIR, exist_ok=True)
os.makedirs(OGDIR, exist_ok=True)

today = datetime.date.today().isoformat()
added, skipped = [], 0
for f in sorted(glob.glob(os.path.join(MAIN, "data", "blog_extra", "*.json"))):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    slug = str(d.get("slug") or os.path.basename(f)[:-5]).strip()
    if not slug:
        continue
    dst = os.path.join(ARTDIR, slug + ".json")
    if os.path.exists(dst):
        skipped += 1
        continue
    og_rel = f"/assets/og/b-{slug}.png"
    rec = {
        "slug": slug,
        "title": d.get("title") or slug,
        "desc": d.get("desc") or "",
        "category": d.get("category") or "Руководство",
        "read_min": 6,
        "date": today,
        "og": og_rel,
        "section": "blog",
        "body_html": d.get("body_html") or d.get("body") or "",
        "extra_html": "",
        "headings": [],
    }
    with open(dst, "w", encoding="utf-8") as w:
        json.dump(rec, w, ensure_ascii=False)
    og = os.path.join(MAIN, "assets", "og", f"b-{slug}.png")
    if os.path.exists(og):
        shutil.copy(og, os.path.join(OGDIR, f"b-{slug}.png"))
    added.append(slug)

print(f"sync: добавлено {len(added)}, уже есть {skipped}")
for s in added:
    print("  +", s)
