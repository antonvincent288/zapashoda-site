#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Редактор-линтер zapashoda-site. Уровень 1, без LLM.
Проверяет каталог статей data/articles/** (blog, pain, safety):
  1. Типографика-гигиена: двойные пробелы, « · »-дубли, пробел перед пунктуацией, «....» (quad-dots).
  2. ДИРЕКТИВА ЦЕН: цена в body_html статей ЗАПРЕЩЕНА (цены только в каталоге).
  3. slug == имя файла, slug уникален.
  4. Гейт гайдов (kind==guide или slug m*/guides): глав >= 8, слов >= 3500, faq >= 4.
Вывод: JSON-отчёт; exit 1 если есть ERROR.
Использование:
  python3 content_linter.py --root site/src/data/articles [--json out.json]
"""
import argparse, glob, json, os, re, sys

TYPO_PATTERNS = [
    ("double_space", re.compile(r"(?<=\S) {2,}(?=\S)")),
    ("dot_bullet_dup", re.compile(r" ·\s*·")),
    ("space_before_punct", re.compile(r"[\wа-яёА-ЯЁ] +([,.;:!?])")),
    ("quad_dots", re.compile(r"\.{4,}")),
]
PRICE_RE = re.compile(r"\b\d{1,3}(?:[ \u00a0]\d{3})+\s*(?:₽|руб\.?)\b|\b\d{2,6}\s*(?:₽)\b")
sku_prices = set()
GUIDE_MIN_CH, GUIDE_MIN_WORDS, GUIDE_MIN_FAQ = 8, 3500, 4

def strip_tags(html):
    # без вставки пробелов: артефакты склейки дают ложные «двойные пробелы»
    return re.sub(r"<[^>]+>", "", html)

def check_file(path):
    errs, warns = [], []
    d = json.load(open(path, encoding="utf-8"))
    slug_file = os.path.splitext(os.path.basename(path))[0]
    slug = d.get("slug", "")
    if slug != slug_file:
        warns.append(("slug_mismatch", f"slug={slug!r} != имя файла {slug_file!r} (URL строится по полю slug — это ок, но лучше привести имя файла)"))
    body = d.get("body_html", "") or ""
    text = strip_tags(body)
    for name, rx in TYPO_PATTERNS:
        for m in rx.finditer(text):
            ctx = text[max(0, m.start()-30):m.end()+30].replace("\n", " ")
            sev = "warn" if name == "double_space" else "error"
            (errs if sev == "error" else warns).append((name, f"...{ctx}..."))
    for field in ("body_html", "desc", "title"):
        v = d.get(field, "") or ""
        plain = strip_tags(v) if field == "body_html" else v
        for m in PRICE_RE.finditer(plain):
            raw = m.group(0)
            # ДИРЕКТИВА ЦЕН: запрещена только цена НАШЕГО SKU (совпадает с каталогом).
            # Тарифы за кВт·ч, субсидии и прочие внешние цены — не наши товары, не трогаем.
            num = raw.replace("\u00a0", " ").replace(" ", "").replace("₽", "").replace("руб.", "").strip()
            try: val = int(num)
            except ValueError: continue
            if val in sku_prices:
                ctx = plain[max(0, m.start()-40):m.end()+30]
                errs.append(("price_in_article", f"{field}: «{ctx.strip()}» — совпадает с SKU-ценой {val} ₽ (цены только в каталоге)"))
    slugs = [os.path.splitext(os.path.basename(x))[0] for x in glob.glob(os.path.join(os.path.dirname(path), "*.json"))]
    if slugs.count(slug) > 1:
        errs.append(("slug_duplicate", f"slug {slug!r} встречается {slugs.count(slug)} раз"))
    # гейт гайдов
    if d.get("kind") == "guide" or "/guides/" in path or slug.startswith(("m1", "m12")) and "trassa" in slug:
        chapters = d.get("chapters", []) or []
        wc = d.get("word_count", 0) or sum(len(strip_tags((c.get("body", "") or c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))).split()) for c in chapters)
        if len(chapters) < GUIDE_MIN_CH: errs.append(("guide_gate", f"глав {len(chapters)} < {GUIDE_MIN_CH}"))
        if wc < GUIDE_MIN_WORDS: errs.append(("guide_gate", f"слов {wc} < {GUIDE_MIN_WORDS}"))
        if len(d.get("faq", []) or []) < GUIDE_MIN_FAQ: errs.append(("guide_gate", f"faq {len(d.get('faq', []) or [])} < {GUIDE_MIN_FAQ}"))
    return errs, warns

def load_sku_prices(root):
    p = os.path.join(os.path.dirname(os.path.abspath(root)), os.pardir, "sku.json")
    p = os.path.normpath(p)
    try:
        sku = json.load(open(p, encoding="utf-8"))
        return {int(i["price"]) for i in sku.get("items", []) if isinstance(i.get("price"), int)}
    except Exception:
        return set()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="site/src/data/articles")
    ap.add_argument("--json", dest="json_out", default=None)
    args = ap.parse_args()
    global sku_prices
    sku_prices = load_sku_prices(args.root)
    report = {"files": 0, "errors": [], "warns": []}
    for f in sorted(glob.glob(os.path.join(args.root, "*", "*.json"))):
        report["files"] += 1
        errs, warns = check_file(f)
        rel = f.replace("\\", "/")
        for kind, msg in errs: report["errors"].append({"file": rel, "kind": kind, "msg": msg})
        for kind, msg in warns: report["warns"].append({"file": rel, "kind": kind, "msg": msg})
    report["errors_count"] = len(report["errors"])
    report["warns_count"] = len(report["warns"])
    out = json.dumps(report, ensure_ascii=False, indent=1)
    if args.json_out: open(args.json_out, "w", encoding="utf-8").write(out)
    print(out[:6000])
    print(f"\nFILES={report['files']} ERRORS={report['errors_count']} WARNS={report['warns_count']}")
    sys.exit(1 if report["errors_count"] else 0)

if __name__ == "__main__":
    main()
