#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Харнесс агентского конвейера zapashoda.
1) Валидирует драфты статей bridge/drafts/articles/*.json: схема, объём, ссылки, сборка сайта, OG.
   Зелёные переносит в data/blog_extra/ и пушит (деплой триггерится site.yml). Красные остаются.
2) Валидирует код-драфты bridge/drafts/code/*.patch: git apply -> py_compile -> build.
   Красные не применяются. Всё докладывает в мост (bridge/architect_to_alisa.json)."""
import json, os, re, sys, subprocess, base64, tempfile, py_compile, html as _html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from architect_bot import req, get_file, push_files, REPO, BR
import datetime, urllib.request

TZ = datetime.timezone(datetime.timedelta(hours=3))
def now(): return datetime.datetime.now(TZ).isoformat(timespec="seconds")
ALLOWED_EXTS = ("build.py", "services.py", "catalog.py", "artv3.py")
def strip_tags(s): return re.sub(r"<[^>]+>", " ", s)
def plain_words(s):
    txt = _html.unescape(strip_tags(s))
    return len([w for w in re.split(r"\W+", txt) if w])
def internal_hrefs(html_text):
    out = set()
    for m in re.finditer(r"href=['\"](/[^'\"]+)['\"]", html_text):
        p = m.group(1).split("#")[0]
        if p and not p.startswith("//"): out.add(p)
    return out
def pycompile_all():
    for f in ALLOWED_EXTS:
        py_compile.compile(f, doraise=True)
def build_site(outdir="_site_check"):
    r = subprocess.run([sys.executable, "build.py", outdir], capture_output=True, text=True, timeout=900)
    if r.returncode != 0: raise RuntimeError("сборка упала:\n" + (r.stdout + r.stderr)[-1500:])
    return r.stdout + r.stderr
def sitemap_paths(outdir="_site_check"):
    xml = open(os.path.join(outdir, "sitemap.xml"), encoding="utf-8").read()
    paths = set(u.split("//", 1)[1].split("/", 1)[1] if "/" in u.split("//",1)[1] else "" for u in re.findall(r"<loc>([^<]+)</loc>", xml))
    return {("/" + p).rstrip("/") for p in paths}
def link_ok(path, spaths, outdir="_site_check"):
    if path in spaths: return True
    if path.endswith(".html"):
        return os.path.exists(os.path.join(outdir, path.lstrip("/")))
    return (os.path.exists(os.path.join(outdir, path.lstrip("/"), "index.html"))
            or os.path.exists(os.path.join(outdir, path.lstrip("/")) + ".html"))
def next_v_id(a2z):
    nums = [int(m.group(1)) for m in (re.match(r"V-(\d+)", x.get("id","")) for x in a2z.get("messages", [])) if m]
    return max(nums + [0]) + 1
def validator_msg(topic, body):
    a2z_raw = get_file(BR + "/architect_to_alisa.json") or '{"protocol":"zapashoda-bridge-v1","messages":[]}'
    a2z = json.loads(a2z_raw)
    a2z.setdefault("messages", []).append({"id": "V-%04d" % next_v_id(a2z), "ts": now(), "from": "validator",
        "topic": topic[:120], "body": body[:3000], "priority": "normal", "expect": "answer", "answer_to": None})
    return a2z
def main():
    notes = []
    draft_dir = os.path.join(BR, "drafts", "articles")
    code_dir = os.path.join(BR, "drafts", "code")
    applied, rejected = [], []
    os.makedirs("data/blog_extra", exist_ok=True)
    drafts = []
    if os.path.isdir(draft_dir):
        for fn in sorted(os.listdir(draft_dir)):
            if fn.endswith(".json"):
                try: drafts.append((fn, json.load(open(os.path.join(draft_dir, fn), encoding="utf-8"))))
                except Exception as e: rejected.append((fn, "битый JSON: %r" % e))
    if not drafts and not os.path.isdir(code_dir):
        print("драфтов нет — нечего валидировать"); return
    # --- статьи ---
    if drafts:
        try: pycompile_all()
        except Exception as e:
            print("py_compile НЕ ПРОШЁЛ:", repr(e)[:300], "— применяемые драфты отменяются"); sys.exit(1)
        existing = set()
        sp = open("services.py", encoding="utf-8").read()
        b0 = sp.find("BLOG_ARTICLES = ["); b1 = sp.find("\n]", b0)
        existing |= set(re.findall(r"\('([a-z0-9-]+)',", sp[b0:b1]))
        existing |= {fn[:-5] for fn in os.listdir("data/blog_extra") if fn.endswith(".json")}
        for fn, d in drafts:
            slug = str(d.get("slug", "")).strip()
            errs = []
            if not re.match(r"^[a-z0-9-]{5,64}$", slug): errs.append("bad slug")
            if slug in existing: errs.append("slug уже существует")
            t = str(d.get("title", "")).strip(); desc = str(d.get("desc", "")).strip(); body = str(d.get("body_html", "")).strip()
            if not (10 <= len(t) <= 57): errs.append("title %d симв (нужно 10–57)" % len(t))
            if not (80 <= len(desc) <= 300): errs.append("desc %d симв (нужно 80–300)" % len(desc))
            w = plain_words(body)
            if w < 500: errs.append("мало слов в теле: %d (нужно 500+)" % w)
            if w > 2200: errs.append("слишком длинно: %d слов" % w)
            if body.count("<h2") < 2: errs.append("меньше 2 секций h2")
            links = [h for h in internal_hrefs(body)]
            if len(links) < 3: errs.append("меньше 3 внутренних ссылок")
            if "<script" in body.lower(): errs.append("script запрещён")
            if body.count("₽") > 6: errs.append("больше 6 вхождений ₽ — возможна выдуманная цена")
            if re.search(r"\b(api[_-]?key|token|password|secret)\b", body.lower()): errs.append("подозрение на секрет в тексте")
            if errs: rejected.append((fn, "; ".join(errs))); continue
            os.makedirs("data/blog_extra", exist_ok=True)
            json.dump(d, open(os.path.join("data/blog_extra", slug + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            applied.append((fn, slug, t))
        if applied:
            log = build_site()
            sm = sitemap_paths()
            for fn, slug, t in applied:
                page = os.path.join("_site_check", "blog", slug + ".html")
                if not os.path.exists(page):
                    rejected.append((fn, "страница не собралась")); continue
                doc = open(page, encoding="utf-8").read()
                bad = [h for h in internal_hrefs(doc) if not link_ok(h, sm)]
                if bad: rejected.append((fn, "битые внутренние ссылки: " + ", ".join(sorted(bad)[:5]))); continue
                print("GREEN:", slug)
        final = [a for a in applied if not any(r[0] == a[0] for r in rejected)]
        for fn, slug, t in final:
            try: os.remove(os.path.join(draft_dir, fn))
            except Exception: pass
    # --- код-драфты ---
    code_applied = []
    if os.path.isdir(code_dir):
        for fn in sorted(os.listdir(code_dir)):
            if not fn.endswith(".patch"): continue
            patch = open(os.path.join(code_dir, fn), encoding="utf-8").read()
            r = subprocess.run(["git", "apply", "--check", os.path.join(code_dir, fn)], capture_output=True, text=True)
            if r.returncode != 0:
                rejected.append((fn, "git apply: " + (r.stderr or "").strip()[:200])); continue
            subprocess.run(["git", "apply", os.path.join(code_dir, fn)], capture_output=True, text=True)
            try:
                pycompile_all()
            except Exception as e:
                rejected.append((fn, "py_compile после патча: %r" % e)); continue
            try:
                build_site("_site_check_code")
            except Exception as e:
                rejected.append((fn, str(e)[:300])); continue
            code_applied.append((fn, patch))
    # --- пуш результата ---
    files = {}
    for fn, slug, t in final:
        d = json.load(open(os.path.join("data/blog_extra", slug + ".json"), encoding="utf-8"))
        files["data/blog_extra/%s.json" % slug] = json.dumps(d, ensure_ascii=False, indent=1)
    if code_applied:
        for fn, _patch in code_applied:
            try: os.remove(os.path.join(code_dir, fn))
            except Exception: pass
        subprocess.run(["git", "add", "-A"], capture_output=True)
        subprocess.run(["git", "commit", "-m", "bot-patch: применён %s (валидация зелёная)" % fn], capture_output=True)
        subprocess.run(["git", "push"], capture_output=True)
        print("код-драфт применён и запушен git-ом:", fn)
        fn = None
    if files or rejected or code_applied:
        if final: notes.append("Принято и опубликовано: " + ", ".join(sl for _, sl, _ in final))
        if rejected: notes.append("Отклонено: " + "; ".join("%s (%s)" % (f, r[:160]) for f, r in rejected))
        a2z = validator_msg("Валидатор драфтов", "\n".join(notes) if notes else "без изменений")
        files[BR + "/architect_to_alisa.json"] = json.dumps(a2z, ensure_ascii=False, indent=2)
        if files:
            sha = push_files(files, "validator: драфты (%d принято, %d отклонено)" % (len(final), len(rejected)))
            print("pushed", sha[:12])
    print("итог: принято", len(final), "| отклонено", len(rejected))
if __name__ == "__main__":
    main()
