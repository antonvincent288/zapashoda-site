#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Стажёр-разработчик zapashoda (Groq llama-3.3-70b-versatile).
Пишет код-драфты (unified diff) в bridge/drafts/code/. НЕ пушит код сам — только драфты.
Применение и проверка — в scripts/validate_drafts.py."""
import json, os, re, time, base64, datetime, urllib.request, urllib.error
sys_path = os.path.dirname(os.path.abspath(__file__))
import sys; sys.path.insert(0, sys_path)
from architect_bot import req, get_file, push_files, REPO, BR
GROQ_KEY = os.environ.get("GROQ_API_KEY") or ""
MODEL = "llama-3.3-70b-versatile"
SYSTEM = """Ты — стажёр-разработчик репозитория zapashoda-site. Твоя задача — предложить патч (unified diff)
для конкретной мелкой задачи. Жёсткие правила: 1) только unified diff в формате `diff --git a/<path> b/<path>`;
2) не выдумывай контекст, которого нет в предоставленном коде; 3) бизнес-константы (цены, тарифы) НЕ менять;
4) секреты не упоминать; 5) минимальный дифф, без рефакторинга; 6) ответ — ТОЛЬКО дифф, без пояснений."""
def groq(prompt):
    if not GROQ_KEY: raise RuntimeError("GROQ_API_KEY недоступен")
    body = {"model": MODEL, "temperature": 0.1, "max_tokens": 2000,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}
    for attempt in range(3):
        st, d = req("https://api.groq.com/openai/v1/chat/completions", "POST", body,
                    headers={"Authorization": "Bearer " + GROQ_KEY, "Content-Type": "application/json"})
        if st == 429: time.sleep(20); continue
        if st == 200 and isinstance(d, dict) and d.get("choices"):
            return d["choices"][0]["message"]["content"]
        time.sleep(10)
    raise RuntimeError("Groq недоступен (st=%s)" % st)
def find_pdf_dupes(bp):
    lines = bp.split("\n")
    dup = []
    for i in range(len(lines) - 1):
        a, b = lines[i].strip(), lines[i+1].strip()
        if a and a == b and len(a) > 40 and ("copytree" in a or "paket" in a.lower() or "b2b" in a.lower()):
            dup.append((i+1, lines[i]))
    return dup
def build_prompt():
    bp = get_file("build.py") or ""
    roadmap = get_file(BR + "/roadmap.md") or ""
    dupes = find_pdf_dupes(bp)
    ctx = ""
    for ln, line in dupes[:4]:
        s = max(0, ln-3); e = min(len(bp.split("\n")), ln+3)
        ctx += "\n\n=== строки %d-%d build.py ===\n" % (s+1, e) + "\n".join(bp.split("\n")[s:e])
    return "Дорожная карта (контекст):\n%s\n\nВ build.py найден дублирующийся блок копирования PDF: %s\n%s\n\nЗадача: подготовь unified diff, который УДАЛЯЕТ один из дублирующихся блоков (оставив один). Патч должен применяться git apply." % (roadmap[:2500], dupes[:3], ctx[:4000])
def main():
    try:
        diff = groq(build_prompt())
    except Exception as e:
        print("dev-bot:", repr(e)); return
    diff = re.sub(r"```(?:diff)?", "", str(diff)).strip()
    if not diff.startswith("diff --git"):
        print("dev-bot: ответ не дифф — пропущено"); return
    slug = "dev-%s" % datetime.datetime.now().strftime("%m%d%H%M")
    path = BR + "/drafts/code/" + slug + ".patch"
    sha = push_files({path: diff[:20000]}, "dev-bot: драфт патча " + slug)
    print("dev draft:", slug, "| pushed", sha[:12])
if __name__ == "__main__":
    main()
