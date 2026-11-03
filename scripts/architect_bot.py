#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Архитектор-бот zapashoda v2 (Pollinations GPT-OSS 20B) — режим «стажёра».
Каждый прогон: (1) совет/ответ в мост, (2) через 55 с — драфт статьи в bridge/drafts/articles/.
Секретов не читает и не пишет; код не пушит. Всё фактическое — только из facts_pack."""
import json, os, re, time, base64, datetime, urllib.request, urllib.error

REPO = os.environ.get("GITHUB_REPOSITORY") or "antonvincent288/zapashoda-site"
TOKEN = os.environ.get("GITHUB_TOKEN") or ""
POLLINATIONS_MODEL = "openai-fast"
FALLBACK_MODEL = "openai"
BR = "bridge"
TOPICS = [
 "плата за простой на зарядных станциях: сессия закончилась, счёт капает — что делать владельцу",
 "станция отдаёт меньше заявленной мощности: 150 кВт против реальных 60-80 — почему и как смотреть",
 "«китайское время» в расписании зарядки после русификации: как чинить простыми шагами",
 "потери при зарядке 5–10%: куда уходят ватты и как их вернуть практическими приёмами",
 "зимнее хранение электромобиля: парковка на 2–4 недели без разряда батареи",
 "как выбрать тариф для домашней зарядки: ночной/дневной счётчик и реальная экономия",
]
def req(url, method="GET", data=None, headers=None, timeout=90):
    h = {"User-Agent": "architect-bot/2.0", "Accept": "application/vnd.github+json"}
    h.update(headers or {})
    if TOKEN: h["Authorization"] = "token " + TOKEN
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout); raw = resp.read()
        try: return resp.status, json.loads(raw)
        except Exception: return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, json.loads(raw)
        except Exception: return e.code, raw
def blob_sha(content):
    st, b = req("https://api.github.com/repos/%s/git/blobs" % REPO, "POST",
        {"content": base64.b64encode(content.encode("utf-8")).decode(), "encoding": "base64"})
    assert st == 201, (st, b)
    return b["sha"]
def get_file(path):
    st, ref = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO)
    if st != 200: return None
    head = ref["object"]["sha"]
    st, c = req("https://api.github.com/repos/%s/git/commits/%s" % (REPO, head))
    if st != 200: return None
    st, t = req("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, c["tree"]["sha"]), "GET")
    if st != 200: return None
    it = next((x for x in t["tree"] if x["path"] == path), None)
    if not it: return None
    st, bl = req("https://api.github.com/repos/%s/git/blobs/%s" % (REPO, it["sha"]))
    if st != 200: return None
    return base64.b64decode(bl["content"]).decode("utf-8")
def push_files(files, message):
    for attempt in range(3):
        st, ref = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO)
        head = ref["object"]["sha"]
        st, c = req("https://api.github.com/repos/%s/git/commits/%s" % (REPO, head))
        items = [{"path": p, "mode": "100644", "type": "blob", "sha": blob_sha(cnt)} for p, cnt in files.items()]
        st, tree = req("https://api.github.com/repos/%s/git/trees" % REPO, "POST",
            {"base_tree": c["tree"]["sha"], "tree": items})
        assert st == 201, (st, tree)
        st, newc = req("https://api.github.com/repos/%s/git/commits" % REPO, "POST",
            {"message": message, "tree": tree["sha"], "parents": [head]})
        assert st == 201, (st, newc)
        st, _ = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO, "PATCH",
            {"sha": newc["sha"], "force": False})
        if st == 200: return newc["sha"]
        time.sleep(8)
    raise RuntimeError("не удалось запушить (гонка)")
def pollinations(system, prompt, max_tokens=1100):
    body = {"model": POLLINATIONS_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": 0.4, "max_tokens": max_tokens, "private": True}
    for attempt in range(4):
        st, d = req("https://text.pollinations.ai/openai", "POST", body, headers={"Content-Type": "application/json"})
        if st == 429: time.sleep(50); continue
        if st == 200 and isinstance(d, dict) and d.get("choices"):
            return d["choices"][0]["message"]["content"]
        if st == 200: body["model"] = FALLBACK_MODEL
        time.sleep(10)
    raise RuntimeError("Pollinations недоступен")
def parse_json(text):
    text = re.sub(r"```(?:json)?", "", str(text)).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m: return None
    raw = m.group(0)
    raw = re.sub(r",(\s*[}\]])", r"\1", raw)  # висячие запятые
    try: return json.loads(raw)
    except Exception: return None
SYSTEM = """Ты — архитектор проекта zapashoda-ev.ru (зарядные аксессуары для электромобилей).
Твоя работа: советы, планирование и ревью. ТЫ НЕ ПИШЕШЬ КОД и не меняешь сайт.
Жёсткие правила: 1) ни одного выдуманного факта — если данных нет, пиши «нужно уточнить у владельца»;
2) цены НЕ придумывать — писать [ЦЕНА: согласовать с владельцем]; 3) секреты не упоминать;
4) отвечай СТРОГО одним JSON-объектом: {"topic": "...", "body": "...", "priority": "normal", "expect": "answer"};
5) по-русски, по делу, до ~1200 знаков; 6) в body всегда добавляй строку «План следующего шага: ...»."""
DRAFT_SYSTEM = """Ты — автор экспертных статей блога zapashoda-ev.ru (зарядка и аксессуары для электромобилей в России).
Пиши СТРОГО один JSON-объект без markdown-обёрток:
{"slug": "kejs-v-latine", "title": "...", "desc": "...", "category": "Гайд", "body_html": "...", "faq": [["вопрос","ответ"],["вопрос","ответ"]]}
Правила:
1. ФАКТЫ — только из предоставленного facts_pack. Никаких цифр, которых там нет. Где нужна цена — пиши [ЦЕНА: согласовать с владельцем] или вообще обойди без денег.
2. Внутренние ссылки — ТОЛЬКО из списка ALLOWED_LINKS (не менее 3 на статью, разные).
3. body_html — чистый HTML: <h2> (минимум 2), <p>, <ul>/<li>, <table> разрешены; БЕЗ <script>, <style>, <img>; 550–900 слов; живой практичный тон, обращение к читателю; финальный h2 с практическим выводом.
4. title 30–55 символов, desc 120–240 символов, slug — латиница с дефисами, уникальный.
5. faq — 2–4 пары по теме.
6. Не пиши оглавление-заглушку «Оглавление», не добавляй CTA-кнопки."""
ALLOWED_LINKS = ["/pain/adapter-gbt.html", "/pain/stoimost-zaryadki.html", "/pain/zaryadka-na-trasse.html", "/pain/domashnie-stancii.html", "/pain/zaryadka-ot-rozetki.html", "/pain/podogrev-batarei.html", "/pain/zapas-hoda-zimoy.html", "/pain/ne-zaryazhaetsya.html", "/pain/udlinitel.html", "/pain/12v-akb.html", "/calculator/", "/charging/", "/catalog/", "/blog/", "/vin/", "/models/zeekr-001-001-fr.html", "/models/li-auto-l6-l7-l8-l9-2022-2025.html", "/models/voyah-free-evr-gibrid.html", "/models/byd-song-plus-ev.html", "/blog/subsidii-na-elektromobil-2026.html", "/blog/transportnyi-nalog-elektromobilya.html", "/blog/zimnyaya-zaryadka-medlennee.html", "/blog/stanciya-ne-rabotae t.html".replace(" ", ""), "/blog/handshake-oshibka-dc-zaryadki.html", "/blog/skolko-zhivet-batareya-elektromobilya.html"]
def blog_slugs():
    try:
        sp = get_file("services.py") or ""
        b0 = sp.find("BLOG_ARTICLES = ["); b1 = sp.find("\n]", b0)
        return set(re.findall(r"\('([a-z0-9-]+)',", sp[b0:b1]))
    except Exception:
        return set()
def blog_index_links():
    return ["/blog/" + s + ".html" for s in sorted(blog_slugs())]
def do_advice():
    roadmap = get_file(BR + "/roadmap.md") or ""
    ai = get_file("AI_BRIDGE.json") or "{}"
    a2z = json.loads(get_file(BR + "/architect_to_alisa.json") or '{"protocol":"zapashoda-bridge-v1","messages":[]}')
    z2a = json.loads(get_file(BR + "/alisa_to_architect.json") or '{"protocol":"zapashoda-bridge-v1","messages":[]}')
    try: state = json.loads(get_file(BR + "/architect_state.json") or "{}")
    except Exception: state = {}
    def z_num(mid):
        m = re.match(r"Z-(\d+)", str(mid or ""))
        return int(m.group(1)) if m else -1
    last_z = state.get("last_alisa_id", "")
    pending = [m for m in z2a.get("messages", []) if m.get("from") == "alisa" and z_num(m.get("id")) > z_num(last_z)]
    ctx_pending = "\n\n".join("id=%s | topic=%s\n%s" % (m.get("id"), m.get("topic"), (m.get("body") or "")[:1200]) for m in pending[-3:])
    ctx_mine = "\n\n".join("id=%s: %s" % (m.get("id"), (m.get("body") or "")[:300]) for m in a2z.get("messages", [])[-3:])
    nums = [int(m.group(1)) for m in (re.match(r"A-(\d+)", x.get("id", "")) for x in a2z.get("messages", [])) if m]
    next_num = max(nums + [0]) + 1
    prompt = "Состояние (roadmap):\n%s\n\nAI_BRIDGE:\n%s\n\nМои последние ответы:\n%s\n\nНовые сообщения Алисы (%d):\n%s\n\nЗадача: %s\nВерни СТРОГО JSON." % (
        roadmap[:5000], ai[:1000], ctx_mine, len(pending), ctx_pending or "(нет)",
        "ответь на последнее сообщение Алисы" if pending else "дай один полезный статус-совет по текущему этапу; без выдуманного прогресса")
    content = pollinations(SYSTEM, prompt)
    parsed = parse_json(content) or {"topic": "Совет архитектора", "body": str(content)[:1500], "priority": "normal", "expect": "answer"}
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(timespec="seconds")
    msg = {"id": "A-%04d" % next_num, "ts": ts, "from": "architect",
           "topic": str(parsed.get("topic", "Без темы"))[:120], "body": str(parsed.get("body", content))[:4000],
           "priority": parsed.get("priority") if parsed.get("priority") in ("normal", "high") else "normal",
           "expect": "answer", "answer_to": (pending[-1]["id"] if pending else None)}
    a2z.setdefault("messages", []).append(msg)
    state["last_alisa_id"] = (pending[-1]["id"] if pending else last_z) or ""
    sha = push_files({BR + "/architect_to_alisa.json": json.dumps(a2z, ensure_ascii=False, indent=2),
                      BR + "/architect_state.json": json.dumps(state, ensure_ascii=False, indent=2)},
                     "architect-bot: %s" % msg["id"])
    print("advice:", msg["id"], "|", msg["topic"], "| pushed", sha[:12])
def do_draft():
    fp = get_file("data/facts_pack.json")
    if not fp:
        print("facts_pack отсутствует — драфт пропущен"); return
    existing = blog_slugs()
    topic = TOPICS[int(datetime.datetime.now().timestamp() // 60) % len(TOPICS)]
    prompt = "facts_pack.json:\n%s\n\nУже есть статьи (слаги): %s\n\nРазрешённые внутренние ссылки:\n%s\n\nТема статьи (если по ней уже есть статья — выбери сам ближайшую неосвещённую тему из своих знаний, но факты всё равно только из facts_pack): %s\n\nНапиши статью по формату из системной инструкции." % (
        fp, ", ".join(sorted(existing))[:2500], ", ".join(ALLOWED_LINKS + blog_index_links()), topic)
    content = pollinations(DRAFT_SYSTEM, prompt, max_tokens=2600)
    d = parse_json(content)
    if not d or not d.get("slug") or not d.get("body_html"):
        print("драфт: модель не вернула валидный JSON — пропущено"); return
    slug = str(d["slug"]).strip()
    if slug in existing:
        print("драфт: slug уже существует — пропущено"); return
    path = BR + "/drafts/articles/" + slug + ".json"
    if get_file(path) is not None:
        print("драфт уже есть:", slug); return
    sha = push_files({path: json.dumps(d, ensure_ascii=False, indent=1)}, "architect-bot: драфт статьи " + slug)
    print("draft:", slug, "| pushed", sha[:12])
def main():
    do_advice()
    time.sleep(55)  # лимит Pollinations 1 запрос / 45 с
    try: do_draft()
    except Exception as e:
        print("draft step failed:", repr(e))
if __name__ == "__main__":
    main()
