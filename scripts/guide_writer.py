#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Турбо-писатель гайдов zapashoda: матричный воркер (по одному гайду на джоб).
Глава за главой через Pollinations (GPT-OSS 20B, reasoning low), с чекпойнтами в
bridge/turbo_state.json. Платные гайды НЕ публикуются сами — только черновики в
bridge/drafts/guides/ на согласование владельцу. Без выдуманных фактов и цен."""
import json, os, re, sys, time, base64, datetime, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# импорт хелперов из архитектора динамически невозможен (файл — копия API-блока ниже)
import argparse
REPO = os.environ.get("GITHUB_REPOSITORY") or "antonvincent288/zapashoda-site"
TOKEN = os.environ.get("GITHUB_TOKEN") or ""
BR = "bridge"
def req(url, method="GET", data=None, headers=None, timeout=120):
    h = {"User-Agent": "turbo-writer/1.0", "Accept": "application/vnd.github+json"}
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
    st, tr = req("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, c["tree"]["sha"]), "GET")
    if st != 200: return None
    it = next((x for x in tr["tree"] if x["path"] == path), None)
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
        st, tr = req("https://api.github.com/repos/%s/git/trees" % REPO, "POST", {"base_tree": c["tree"]["sha"], "tree": items})
        assert st == 201, (st, tr)
        st, newc = req("https://api.github.com/repos/%s/git/commits" % REPO, "POST",
            {"message": message, "tree": tr["sha"], "parents": [head]})
        assert st == 201, (st, newc)
        st, _ = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO, "PATCH", {"sha": newc["sha"], "force": False})
        if st == 200: return newc["sha"]
        time.sleep(8)
    raise RuntimeError("не удалось запушить (гонка)")
ALLOWED_RANGES = {"3–4","3-4","6–9","6-9","10–20","10-20","15–20","15-20","15–25","15-25","18–30","18-30"}
PRICE_PLACEHOLDER = "[ЦЕНА: согласовать с владельцем]"
def scrub_prices(html):
    def rep_range(m):
        a, b = m.group(1).replace(" ", ""), m.group(2).replace(" ", "")
        return (a + "–" + b + " ₽") if (a + "–" + b) in ALLOWED_RANGES else (PRICE_PLACEHOLDER + " ₽")
    html = re.sub(r"(\d[\d\s]*(?:[.,]\d+)?)\s*[–-]\s*(\d[\d\s]*(?:[.,]\d+)?)\s*₽", rep_range, html)
    def rep_single(m):
        n = m.group(1).replace(" ", "")
        if n in ("925", "35"): return m.group(0)
        return PRICE_PLACEHOLDER + " ₽"
    html = re.sub(r"(\d[\d\s]*(?:[.,]\d+)?)\s*₽", rep_single, html)
    return html
def pollinations(system, prompt, max_tokens=8000):
    body = {"model": "openai-fast",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": 0.4, "max_tokens": max_tokens, "private": True, "reasoning_effort": "low"}
    for w in [20, 40, 60, 90, 120]:
        st, d = req("https://text.pollinations.ai/openai", "POST", body, headers={"Content-Type": "application/json"})
        if st == 200 and isinstance(d, dict) and d.get("choices"):
            return d["choices"][0]["message"].get("content") or ""
        print("pollinations attempt status", st); time.sleep(w)
    raise RuntimeError("Pollinations недоступен")
GUIDES = {
 "m11-trassa": {
   "title": "М-11 «Нева»: зарядка электромобиля на трассе в 2026",
   "desc": "Где и как заряжать электромобиль на трассе Москва — Санкт-Петербург: зоны платности, планирование остановок, резервный план.",
   "chapters": [
     "Планирование поездки: как рассчитать остановки для зарядки на 700 км",
     "Как работает бесплатный проезд для электромобилей российской сборки и T-pass",
     "Мультифуэлинг: типы станций на трассе и что везти с собой (кабели, адаптеры)",
     "Куда ставить машину: выбор остановки по времени до следующей зарядки",
     "Что делать, если станция занята или не работает: резервный план",
     "Зимой: мороз, понижение мощности и где ждать прогрева батареи",
     "Оплата на станциях: приложения операторов, подписки и что взять с собой",
     "Чек-лист водителя электромобиля для дальнего маршрута",
   ]},
 "m12-trassa": {
   "title": "М-12 «Восток»: зарядка на трассе Москва — Казань — Екатеринбург",
   "desc": "Практический гайд по зарядке на новой трассе М-12: планирование, мультифуэлинг, резервы, зимний режим.",
   "chapters": [
     "Планирование маршрута: расчёт остановок на длинной дистанции",
     "Бесплатный проезд для электромобилей российской сборки: как это работает",
     "Мультифуэлинг на трассе: DC-зарядки, адаптеры, кабели",
     "Стратегия остановок: когда и где заряжаться без потери времени",
     "Резервный план: что делать при отказе станции",
     "Зимний режим: мощность, прогрев батареи и запас хода",
     "Приложения операторов: как оплачивать и следить за сессией",
     "Чек-лист для дальнего маршрута по М-12",
   ]},
 "parking-zhil": {
   "title": "Зарядка на парковке ЖК: жильё без личной стоянки",
   "desc": "Как заряжать электромобиль в жилом комплексе без собственного парко-места: варианты, договоры с УК, нормы 2026.",
   "chapters": [
     "Проблема: ЖК без личного парко-места — варианты зарядки",
     "Общественные парковки рядом: как искать и проверять станции",
     "Договор с УК и соседи: как легализовать зарядку на территории ЖК",
     "Нормы 2026 (СП 551): что можно на парковке до 32 А",
     "Переносные решения: зарядка от розетки — риски и правила",
     "Аренда парко-места с зарядкой: что спрашивать и как проверять",
     "Тарифы и счётчики: как считается электроэнергия",
     "Чек-лист: как выбрать решение для вашего ЖК",
   ]},
}
CHAPTER_SYS = """Ты — технический автор гайдов zapashoda-ev.ru (зарядка электромобилей в России).
Пишешь ОДИН раздел гайда по указанию. Формат: чистый HTML (один <h2> с темой раздела, <p>, <ul>/<li>,
минимум 1 внутренняя ссылка из списка, 500–750 слов, практичный тон, без <script>/<style>/<img>, без таблиц цен).
Правила: факты только из facts_pack; цены не придумывать — диапазоны из facts_pack с пометкой «ориентир»,
иначе [ЦЕНА: согласовать с владельцем]; секреты не упоминать; живой тон, обращение к читателю."""
LINKS = ", ".join(["/pain/adapter-gbt.html", "/pain/stoimost-zaryadki.html", "/pain/zaryadka-na-trasse.html",
 "/pain/domashnie-stancii.html", "/pain/zaryadka-ot-rozetki.html", "/pain/zapas-hoda-zimoy.html",
 "/pain/podogrev-batarei.html", "/pain/udlinitel.html", "/pain/12v-akb.html", "/calculator/", "/charging/",
 "/catalog/", "/blog/subsidii-na-elektromobil-2026.html", "/blog/transportnyi-nalog-elektromobilya.html",
 "/blog/zimnyaya-zaryadka-medlennee.html", "/blog/stanciya-ne-rabotaet.html", "/blog/handshake-oshibka-dc-zaryadki.html"])
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--guide", required=True)
    args = ap.parse_args()
    g = GUIDES.get(args.guide)
    if not g: print("гайд не найден:", args.guide); return
    fp = get_file("data/facts_pack.json") or "{}"
    state_path = BR + "/turbo_state.json"
    try: state = json.loads(get_file(state_path) or "{}")
    except Exception: state = {}
    gs = state.setdefault("guides", {}).setdefault(args.guide, {"done": []})
    slug = args.guide
    draft_path = BR + "/drafts/guides/" + slug + ".json"
    try: draft = json.loads(get_file(draft_path) or "{}")
    except Exception: draft = {}
    if not draft:
        draft = {"slug": slug, "title": g["title"], "desc": g["desc"], "category": "Гайд",
                 "kind": "paid_guide", "price_pending": True, "chapters": [], "faq": []}
    for i, ch in enumerate(g["chapters"]):
        key = "c%02d" % i
        if key in gs["done"] and i < len(draft["chapters"]):
            continue
        prompt = "facts_pack:\n%s\n\nГайд: «%s»\nРаздел %d из %d: %s\nРазрешённые внутренние ссылки:\n%s\n\nНапиши этот раздел целиком (HTML)." % (fp, g["title"], i + 1, len(g["chapters"]), ch, LINKS)
        html = pollinations(CHAPTER_SYS, prompt)
        html = re.sub(r"^```(?:html)?\s*|\s*```$", "", html.strip())
        html = scrub_prices(html)
        if "<h2" not in html or len(html.split()) < 300:
            print("глава %s слишком коротка (%d слов) — пропущена" % (key, len(html.split())))
            continue
        while len(draft["chapters"]) <= i: draft["chapters"].append("")
        draft["chapters"][i] = html
        gs["done"].append(key)
        # чекпойнт: состояние + черновик
        push_files({draft_path: json.dumps(draft, ensure_ascii=False, indent=1),
                    state_path: json.dumps(state, ensure_ascii=False, indent=1)},
                   "turbo: %s глава %d/%d" % (slug, i + 1, len(g["chapters"])))
        print("глава %d/%d готова (%d слов)" % (i + 1, len(g["chapters"]), len(html.split())))
        time.sleep(50)  # лимит Pollinations
    draft["word_count"] = sum(len(re.sub(r"<[^>]+>", " ", c).split()) for c in draft["chapters"])
    push_files({draft_path: json.dumps(draft, ensure_ascii=False, indent=1)}, "turbo: %s черновик завершён (%d слов)" % (slug, draft["word_count"]))
    print("ЧЕРНОВИК ГОТОВ:", slug, "| слов:", draft["word_count"])
if __name__ == "__main__":
    main()
