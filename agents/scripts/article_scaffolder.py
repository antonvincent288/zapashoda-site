#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Каркасист: болванка статьи/гайда в формате data/articles/**.
Не пушит — пишет файл рядом (--out), дальше линтер и владелец.
Проверяет дубль slug по каталогу и валидность структуры (shortbox-совместимый h2 id=s1).
Использование:
  python3 article_scaffolder.py --slug moy-gaid --title "Заголовок" --section blog \
      [--desc "Короткое описание"] [--category Гайд] [--out /tmp/moy-gaid.json] [--guide]
"""
import argparse, glob, json, os, re, sys, datetime

TODAY = datetime.date.today().isoformat()

def scaffold(args):
    slug = re.sub(r"[^a-z0-9-]", "-", args.slug.lower().strip("-"))
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", slug):
        return None, f"BAD_SLUG: {slug!r}"
    for f in glob.glob("site/src/data/articles/*/*.json"):
        if os.path.splitext(os.path.basename(f))[0] == slug:
            return None, f"SLUG_TAKEN: {f}"
    sections = []
    if args.guide:
        for i in range(1, 9):
            sections.append(f"<h2 id=\"s{i}\">Раздел {i}: [заполнить]</h2>\n<p>[Заполнить главу {i}. Минимум 420 слов на главу — гейт гайдов: 8 глав, 3500 слов, 4 FAQ.]</p>")
    else:
        sections.append('<h2 id="s1">Коротко</h2>\n<p><b>Прямой ответ.</b> [1–3 предложения — суть, без маркетинга]</p>')
        for i, name in enumerate(["Что происходит на самом деле", "Как проверить у себя", "Что делать", "Чего не делать", "Связанные модели", "Что запомнить"], start=2):
            sections.append(f'<h2 id="s{i}">{name}</h2>\n<p>[Заполнить]</p>')
    body = '<div class="art-body">\n' + "\n".join(sections) + "\n</div>"
    headings = [{"id": f"s{i}", "text": re.search(r"<h2[^>]*>([^<]+)", s).group(1)} for i, s in enumerate(sections, start=1)]
    d = {
        "section": args.section, "slug": slug, "title": args.title,
        "desc": args.desc or args.title,
        "category": args.category or ("Гайд" if args.guide else "Разбор"),
        "read_min": 6 if args.guide else 4,
        "date": TODAY,
        "og": f"/assets/og/b-{slug}.png",
        "body_html": body,
        "extra_html": "",
        "headings": headings,
        "faq": [],
    }
    if args.guide:
        d["kind"] = "guide"
        d["chapters"] = [{"h": f"Раздел {i}", "body": ""} for i in range(1, 9)]
    return d, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--desc", default=None)
    ap.add_argument("--section", default="blog", choices=["blog", "pain", "safety"])
    ap.add_argument("--category", default=None)
    ap.add_argument("--guide", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d, err = scaffold(args)
    if err:
        print(json.dumps({"ok": False, "error": err})); sys.exit(1)
    out = args.out or os.path.join(os.getcwd(), args.slug + ".json")
    json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"ok": True, "out": out, "slug": args.slug, "kind": "guide" if args.guide else "article"}))
    print("Дальше: заполнить главы → content_linter.py --json → gh_put_file.py (только с SHA-защитой)")

if __name__ == "__main__":
    main()
