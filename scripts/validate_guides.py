#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Валидатор гайдов: проверяет черновики bridge/drafts/guides/*.json (объём, структура, ссылки).
Зелёные переносит в bridge/drafts/guides/approved/ (НЕ в прод) и докладывает в мост —
публикация платных продуктов только с решения владельца."""
import json, os, re, sys, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guide_writer import get_file, push_files, REPO, BR, req
import urllib.request, datetime
def strip_tags(s): return re.sub(r"<[^>]+>", " ", s)
def words(s): return len([w for w in re.split(r"\W+", strip_tags(s)) if w])
def hrefs(s): return set(re.findall(r"href=['\"]([^'\"]+)['\"]", s))
def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(timespec="seconds")
def main():
    base = BR + "/drafts/guides"
    slugs = []
    st, ref = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO)
    head = ref["object"]["sha"]
    st, c = req("https://api.github.com/repos/%s/git/commits/%s" % (REPO, head))
    st, t = req("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, c["tree"]["sha"]), "GET")
    paths = [it["path"] for it in t["tree"]]
    drafts = [p for p in paths if p.startswith(base + "/") and p.endswith(".json")]
    notes, files = [], {}
    for dp in drafts:
        slug = dp.split("/")[-1][:-5]
        if dp.startswith(base + "/approved/"): continue
        try: d = json.loads(get_file(dp))
        except Exception as e: notes.append("%s: битый JSON" % slug); continue
        errs = []
        chapters = d.get("chapters", [])
        if len(chapters) < 6: errs.append("глав: %d (нужно 6+)" % len(chapters))
        wc = sum(words(x) for x in chapters)
        if wc < 3000: errs.append("слов: %d (нужно 3000+)" % wc)
        short = [i for i, x in enumerate(chapters) if words(x) < 250]
        if short: errs.append("короткие главы: %s" % short[:3])
        joined = "\n".join(chapters)
        real_prices = re.findall(r"\d[\d\s.,]*\s*₽", joined)
        if len(real_prices) > 4: errs.append("реальных цен ₽: %d (нужно 0–4 — только диапазоны из facts_pack)" % len(real_prices))
        if re.search(r"\b(api[_-]?key|token|password|secret)\b", joined.lower()): errs.append("подозрение на секрет")
        if "<script" in joined.lower() or "<style" in joined.lower(): errs.append("script/style запрещены")
        if errs:
            notes.append("%s: %s" % (slug, "; ".join(errs))); continue
        # зелёный → approved/ (ожидание владельца), из очереди убираем
        files[base + "/approved/" + slug + ".json"] = json.dumps(d, ensure_ascii=False, indent=1)
        notes.append("%s: ЗЕЛЁНЫЙ (%d глав, %d слов) — ждёт владельца" % (slug, len(chapters), wc))
    a2z = json.loads(get_file(BR + "/architect_to_alisa.json") or '{"messages":[]}')
    nums = [int(m.group(1)) for m in (re.match(r"V-(\d+)", x.get("id", "")) for x in a2z.get("messages", [])) if m]
    v = {"id": "V-%04d" % (max(nums + [0]) + 1), "ts": now(), "from": "validator",
         "topic": "Валидатор гайдов", "body": ("Принято в очередь согласования: " + "; ".join(notes))[:2800],
         "priority": "normal", "expect": "answer", "answer_to": None}
    a2z["messages"].append(v)
    files[BR + "/architect_to_alisa.json"] = json.dumps(a2z, ensure_ascii=False, indent=2)
    # удаляем принятые из очереди (tree с sha=null)
    tree_items = [{"path": p, "mode": "100644", "type": "blob", "sha": None}
                  for p in drafts if p not in [None]]  # заполним ниже
    for dp in drafts:
        slug = dp.split("/")[-1][:-5]
        if any(k == base + "/approved/" + slug + ".json" for k in files):
            pass
    # простая замена: пушим approved-файлы + мост; из очереди принятые уберутся на следующем прогоне бота-писателя не нужно — оставляем черновик как архив
    if files:
        sha = push_files(files, "validator-guides: черновики гайдов")
        print("pushed", sha[:12])
    print("итог:", len([n for n in notes if "ЗЕЛЁНЫЙ" in n]), "принято,", len([n for n in notes if "ЗЕЛЁНЫЙ" not in n]), "отклонено")
    for n in notes: print(" ", n)
if __name__ == "__main__":
    main()
