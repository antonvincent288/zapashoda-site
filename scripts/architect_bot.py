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
def pollinations(system, prompt, max_tokens=1100, reasoning=None):
    body = {"model": POLLINATIONS_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": 0.4, "max_tokens": max_tokens, "private": True}
    if reasoning: body["reasoning_effort"] = reasoning
    waits = [20, 40, 60, 90, 120, 150]
    for attempt, w in enumerate(waits):
        st, d = req("https://text.pollinations.ai/openai", "POST", body, headers={"Content-Type": "application/json"})
        if st == 429: time.sleep(w); continue
        if st == 200 and isinstance(d, dict) and d.get("choices"):
            return d["choices"][0]["message"]["content"]
        if st == 200: body["model"] = FALLBACK_MODEL
        print("pollinations attempt", attempt + 1, "status", st)
        time.sleep(w)
    raise RuntimeError("Pollinations недоступен после %d попыток" % len(waits))
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
DRAFT_SYSTEM = """Ты — автор статей блога zapashoda-ev.ru (зарядка и аксессуары для электромобилей в России).
Формат ответа СТРОГО такой, без markdown-обёрток:
SLUG: <латиница-с-дефисами>
TITLE: <30-55 символов>
DESC: <120-240 символов>
CATEGORY: Гайд
BODY_HTML:
<чистый HTML статьи: <h2> разделы, <p>, <ul>/<li>, внутренние ссылки только из списка; без <script>/<style>/<img>>
FAQ:
- вопрос | ответ
- вопрос | ответ
Правила: 1) факты — только из facts_pack (чужих цифр не выдумывать); цены не придумывать — диапазоны из facts_pack с пометкой «ориентир» либо [ЦЕНА: согласовать с владельцем]; 2) внутренние ссылки — ТОЛЬКО из списка; 3) практичный живой тон, обращение к читателю; 4) секреты не упоминать; 5) пишешь ЧАСТЬ статьи по указанию в задании — не переписывай уже написанное."""
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
    content = pollinations(SYSTEM, prompt, reasoning="low")
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
def parse_draft(text):
    out = {}
    body_m = re.search(r"BODY_HTML:\s*\n(.*?)\n\s*FAQ:", str(text), re.S)
    if not body_m: return None
    body = body_m.group(1).strip()
    def grab(tag):
        m = re.search(tag + r":\s*(.+)", str(text))
        return m.group(1).strip().strip("`*") if m else ""
    out["slug"] = re.sub(r"[^a-z0-9-]", "-", grab("SLUG").lower())[:64]
    out["title"] = grab("TITLE")
    out["desc"] = grab("DESC")
    out["category"] = grab("CATEGORY") or "Гайд"
    out["body_html"] = re.sub(r"\n\s*", "\n", body)
    faq = []
    for line in str(text).split("\nFAQ:")[-1].splitlines():
        line = line.strip().lstrip("-")
        if "|" in line and len(line) > 15:
            q, a = line.split("|", 1)
            if 5 < len(q.strip()) < 200 and 10 < len(a.strip()) < 400:
                faq.append([q.strip(), a.strip()])
    out["faq"] = faq[:4]
    return out if all(out.get(k) for k in ("slug", "title", "desc", "body_html")) else None
def _headers_from(text):
    def grab(tag):
        m = re.search(tag + r":\s*(.+)", str(text))
        return m.group(1).strip().strip("`*") if m else ""
    return grab("SLUG"), grab("TITLE"), grab("DESC"), grab("CATEGORY")
def _extract_body(text):
    m = re.search(r"BODY_HTML:\s*\n(.*?)(?:\n\s*FAQ:|$)", str(text), re.S)
    if not m: return ""
    return m.group(1).strip()
def _extract_continue(text):
    t = str(text)
    for junk in ("CONTINUE:", "BODY_HTML:"):
        t = t.replace(junk, "")
    t = t.strip()
    if "FAQ:" in t: t = t.split("FAQ:")[0]
    return t.strip() if ("<h2" in t or "<p" in t) else ""
def _extract_faq(text):
    faq = []
    if "\nFAQ:" not in str(text) and not str(text).lstrip().startswith("FAQ:"):
        part = str(text)
    else:
        part = str(text).split("\nFAQ:")[-1]
    for line in part.splitlines():
        line = line.strip().lstrip("-")
        if "|" in line and len(line) > 15:
            q, a = line.split("|", 1)
            if 5 < len(q.strip()) < 200 and 10 < len(a.strip()) < 400:
                faq.append([q.strip(), a.strip()])
    return faq[:4]
LINK_ANCHORS = {
 "/pain/adapter-gbt.html": "Адаптер Type 2 → GB/T: когда нужен и как выбрать",
 "/pain/stoimost-zaryadki.html": "Сколько стоит зарядить электромобиль: полный разбор",
 "/pain/domashnie-stancii.html": "Домашняя зарядная станция: выбор и установка",
 "/pain/zaryadka-ot-rozetki.html": "Зарядка от бытовой розетки: что можно и что нельзя",
 "/pain/podogrev-batarei.html": "Предпрогрев батареи перед быстрой зарядкой",
 "/pain/zapas-hoda-zimoy.html": "Запас хода зимой: почему падает и что делать",
 "/pain/udlinitel.html": "Удлинитель для зарядки: как не сжечь розетку",
 "/pain/12v-akb.html": "12-вольтовый аккумулятор: слабое место EV",
 "/calculator/": "Калькулятор расхода и стоимости поездки",
 "/charging/": "Карта зарядных станций по всей России",
 "/catalog/": "Каталог аксессуаров с подбором по модели",
 "/blog/subsidii-na-elektromobil-2026.html": "Субсидия 35% на электромобиль 2026",
 "/blog/transportnyi-nalog-elektromobilya.html": "Транспортный налог на электромобиль",
}
def ensure_links(body):
    hrefs = set(re.findall(r'href="([^"]+)"', body)) | set(re.findall(r"href='([^']+)'", body))
    if len(hrefs) >= 3: return body
    need = 3 - len(hrefs)
    items = []
    for link, anchor in LINK_ANCHORS.items():
        if link not in hrefs:
            items.append('<li><a href="%s">%s</a></li>' % (link, anchor))
        if len(items) >= need: break
    if items:
        body += "\n<h2>См. также</h2>\n<ul>" + "".join(items) + "</ul>"
    return body
def do_draft():
    fp = get_file("data/facts_pack.json")
    if not fp:
        print("facts_pack отсутствует — драфт пропущен"); return
    existing = blog_slugs()
    links = ", ".join(ALLOWED_LINKS + blog_index_links())
    base_ctx = "facts_pack.json:\n%s\n\nУже есть статьи (слаги): %s\n\nРазрешённые внутренние ссылки:\n%s" % (fp, ", ".join(sorted(existing))[:2200], links)
    # 1) переписать отклонённые валидатором драфты
    a2z = json.loads(get_file(BR + "/architect_to_alisa.json") or '{"messages":[]}')
    rejected = {}
    for m in a2z.get("messages", []):
        if m.get("from") == "validator" and "Отклонено" in (m.get("body") or ""):
            for part in m["body"].split("Отклонено:")[-1].split(";"):
                mm = re.match(r"\s*([a-z0-9-]+)\.json \((.{5,200})\)", part)
                if mm: rejected[mm.group(1)] = mm.group(2)
    targets = []
    for slug, why in rejected.items():
        path = BR + "/drafts/articles/" + slug + ".json"
        if get_file(path):
            targets.append((path, slug, why))
        if len(targets) >= 3: break
    for target in targets:
        path, slug, why = target
        old = json.loads(get_file(path))
        prompt = base_ctx + "\n\nТвоя статья с slug=%s была отклонена валидатором по причинам: %s.\nНапиши её ЗАНОВО и ДЛИННЕЕ: интро + 4–5 разделов h2 по 140–170 слов каждый (в сумме 650–850 слов) + вывод-раздел h2 + FAQ (3 пары).\nОригинальная тема: %s\nУчти причины отклонения (длина, ссылки, заголовок ≤55 символов)." % (slug, why, old.get("title", ""))
        part1 = pollinations(DRAFT_SYSTEM, prompt, max_tokens=6000, reasoning="low")
        h_sl, h_t, h_d, h_c = _headers_from(part1)
        body1 = _extract_body(part1)
        prompt2 = base_ctx + "\n\nПродолжи статью «%s». Уже написано:\n%s\n\nНапиши ТОЛЬКО продолжение: 2–3 новых раздела <h2> (по 140–170 слов, практические шаги) + финальный раздел <h2> с выводом, затем строкой FAQ: и 3 пары «вопрос | ответ». Не повторяй предыдущие разделы, не пиши SLUG/TITLE." % (h_t or old.get("title", ""), body1[:2500])
        part2 = pollinations(DRAFT_SYSTEM, prompt2, max_tokens=8000, reasoning="low")
        body2 = _extract_continue(part2)
        faq = _extract_faq(part2) or _extract_faq(part1)
        slug = old.get("slug", slug)
        d = {"slug": slug, "title": (h_t or old.get("title", ""))[:55], "desc": (h_d or old.get("desc", ""))[:300],
             "category": h_c or old.get("category", "Гайд"),
             "body_html": ensure_links((body1 + "\n" + body2).strip()), "faq": faq}
        if not d["body_html"]:
            print("rewrite: пустое тело — пропущено"); return
        push_files({path: json.dumps(d, ensure_ascii=False, indent=1)}, "architect-bot: переписан драфт " + slug)
        print("rewrite:", slug, "| слов:", len(d["body_html"].split()))
        time.sleep(50)
    # 2) новый драфт: два прохода
    topic = TOPICS[int(datetime.datetime.now().timestamp() // 60) % len(TOPICS)]
    prompt1 = base_ctx + "\n\nТема статьи: %s\nНапиши ПЕРВУЮ ПОЛОВИНУ статьи по формату: интро (130–180 слов) + 2–3 раздела <h2> (по 160–200 слов). Закончи на завершённом абзаце. FAQ не пиши." % topic
    part1 = pollinations(DRAFT_SYSTEM, prompt1, max_tokens=8000, reasoning="low")
    h_sl, h_t, h_d, h_c = _headers_from(part1)
    body1 = _extract_body(part1)
    if not body1:
        print("драфт: первая половина пуста — пропущено"); return
    prompt2 = base_ctx + "\n\nПродолжи статью «%s». Уже написано:\n%s\n\nНапиши ТОЛЬКО продолжение: 2–3 новых раздела <h2> (по 160–200 слов, практические шаги и кейсы) + финальный раздел <h2> с выводом (100–140 слов), затем отдельной строкой FAQ: и 3 пары «вопрос | ответ». Не повторяй предыдущие разделы и заголовки, SLUG/TITLE/DESC не пиши." % (h_t, body1[:2500])
    part2 = pollinations(DRAFT_SYSTEM, prompt2, max_tokens=8000, reasoning="low")
    body2 = _extract_continue(part2)
    faq = _extract_faq(part2) or _extract_faq(part1)
    slug = re.sub(r"[^a-z0-9-]", "-", (h_sl or topic[:40]).lower())[:64]
    title = (h_t or topic)[:55]
    d = {"slug": slug, "title": title, "desc": (h_d or topic)[:300], "category": h_c or "Гайд",
         "body_html": ensure_links((body1 + "\n" + body2).strip()), "faq": faq}
    path = BR + "/drafts/articles/" + slug + ".json"
    if get_file(path) is not None:
        print("драфт уже есть:", slug); return
    sha = push_files({path: json.dumps(d, ensure_ascii=False, indent=1)}, "architect-bot: драфт статьи " + slug)
    print("draft:", slug, "| title:", title, "| слов:", len(d["body_html"].split()), "| pushed", sha[:12])
def main():
    do_advice()
    time.sleep(55)  # лимит Pollinations 1 запрос / 45 с
    try: do_draft()
    except Exception as e:
        print("draft step failed:", repr(e))
if __name__ == "__main__":
    main()
