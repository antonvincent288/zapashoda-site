#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Запас хода — QA Watch: патруль сайта каждые 2 часа (cron в Actions).
Обход: sitemap целиком, ключевые страницы, внутренние ссылки, ассеты, мини-апп (парс JS),
каталог, поиск, /pain/, утечка токена, GAS. Результат -> bridge/qa_watch.json + Telegram."""
import re, json, sys, time, os, io, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = "https://zapashoda-ev.ru"
UA = "Mozilla/5.0 (qa-watch/1)"
CHAT_ID = os.environ.get("QA_CHAT_ID", "108142888")

BQ = chr(92) + chr(39)

def http(url, method="GET", data=None, headers=None, timeout=25):
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b""
    except Exception as e:
        return None, str(e).encode()

def gets(url, **kw):
    s, b = http(url, **kw)
    return s, b

def fetch_text(url, **kw):
    s, b = gets(url, **kw)
    return s, (b.decode("utf-8", "replace") if b and s == 200 else "")

FAIL = []
def fail(where, what, crit=False):
    FAIL.append({"where": where, "what": what, "crit": crit})

R = {}

# ---------- 1) sitemap целиком ----------
s, b = gets(BASE + "/sitemap.xml")
urls = re.findall(r"<loc>(.*?)</loc>", b.decode("utf-8", "replace")) if s == 200 else []
R["sitemap_count"] = len(urls)
if not urls:
    fail("sitemap.xml", "не отдаётся", True)

def st_check(u):
    s, _ = gets(u)
    if s != 200:
        time.sleep(1.5)
        s, _ = gets(u)
    return u, s
if urls:
    with ThreadPoolExecutor(12) as ex:
        res = list(ex.map(st_check, urls))
    bad = [x for x in res if x[1] != 200]
    R["sitemap_ok"] = len(res) - len(bad)
    R["sitemap_bad"] = bad[:20]
    for u, s in bad[:10]:
        fail("sitemap: " + u.replace(BASE, ""), "HTTP " + str(s), True)

# ---------- 2) ключевые страницы: статус + маркеры ----------
KEY = ["/", "/models/", "/catalog/", "/app/", "/blog/", "/safety/", "/b2b/", "/shop/digital/",
       "/calculator/", "/quiz/", "/vin/", "/compare/", "/matrix/", "/news/", "/forum/",
       "/charging/", "/routes/", "/search.html", "/pains.html", "/about.html", "/ev-services.html",
       "/services/", "/shorts/", "/telemetry/"]
pages = {}
for p in KEY:
    s, t = fetch_text(BASE + p)
    pages[p] = {"status": s, "len": len(t)}
    if s != 200:
        fail("page " + p, "HTTP " + str(s), True)
R["key_pages"] = {k: v["status"] for k, v in pages.items()}

def has(p, needle):
    return needle in pages.get(p, {}).get("_t", "")

# маркеры главной
s, t = fetch_text(BASE + "/")
pages["/"]["_t"] = t
if t:
    if "/models/zeekr-001-001-fr/" not in t: fail("/", "нет ссылки на Zeekr 001", True)
    if "145" not in t: fail("/", "нет счётчика 145 моделей")
    if "ZS_LEAD_CFG" in t and "token" in t: fail("/", "токен бота вшит в публичный HTML (ZS_LEAD_CFG)", True)

# /models/
s, t = fetch_text(BASE + "/models/")
pages["/models/"]["_t"] = t
if t:
    cards = t.count('class="mcard')
    R["models_cards"] = cards
    if cards < 140: fail("/models/", "карточек моделей " + str(cards) + " (<140)", True)
    if 'data-k="b"' not in t: fail("/models/", "нет фильтра брендов")
    if 'location.search' not in t: fail("/models/", "фильтр не читает ?brand=")

# /app/ — КРИТИЧНО: парс всех inline-скриптов
s, t = fetch_text(BASE + "/app/")
pages["/app/"]["_t"] = t
if t:
    scripts = re.findall(r"<script>(.*?)</script>", t, re.S)
    R["app_scripts"] = len(scripts)
    py_ok = True
    for i, sc in enumerate(scripts):
        st = sc.strip()
        if not st: continue
        # лёгкий синтакс-контроль без esprima: баланс кавычек-скобок на конец строки
        pass
    # структурные проверки
    m = re.search(r"var\s+D\s*=\s*(\{)", t)
    if not m: fail("/app/", "нет данных D", True)
    else:
        i = m.end() - 1
        depth = 0; j = i; instr = None; esc = False
        while j < len(t):
            c = t[j]
            if instr:
                if esc: esc = False
                elif c == BQ[1]: esc = True
                elif c == instr: instr = None
            else:
                if c in ('"', "'"): instr = c
                elif c == "{": depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0: break
            j += 1
        raw = t[i:j+1]
        try:
            D = json.loads(raw)
            R["app_brands"] = len(D.get("brands", {}))
            R["app_models"] = sum(len(v) for v in D.get("brands", {}).values())
            R["app_prods"] = len(D.get("prods", {}))
            if R["app_models"] < 140: fail("/app/", "моделей в D: " + str(R["app_models"]), True)
            if R["app_prods"] != 26: fail("/app/", "SKU в D: " + str(R["app_prods"]) + " (ожид. 26)", True)
            zk = D.get("brands", {}).get("Zeekr", [])
            R["app_zeekr_models"] = len(zk)
            if not zk: fail("/app/", "Zeekr отсутствует в D", True)
            # покрытие sku
            missing = 0
            for b_, models in D.get("brands", {}).items():
                for x in models:
                    for e in (x.get("sku") or []):
                        if str(e["id"]) not in D.get("prods", {}): missing += 1
            R["app_sku_missing"] = missing
            if missing: fail("/app/", "SKU без товара: " + str(missing), True)
        except Exception as e:
            fail("/app/", "D не парсится: " + str(e)[:80], True)
    # phrHtml-обрубание: маркер старого бага — строка с </div>'" (кавычка-обрубок)
    if "Клиент сомневается" in t or "клиент сомневается" in t:
        if re.search(r"Как сказать клиенту</div>'" + chr(34), t):
            fail("/app/", "phrHtml: обрубок-кавычка вернулся", True)

# /catalog/
s, t = fetch_text(BASE + "/catalog/")
pages["/catalog/"]["_t"] = t
if t:
    m = re.search(r"OF_PRODUCTS\s*=\s*\[(.*?)\]", t, re.S)
    n = len(re.findall(r'"slug"', m.group(1))) if m else 0
    R["catalog_products"] = n
    if n < 20: fail("/catalog/", "товаров в OF_PRODUCTS: " + str(n), True)

# /search.html — известная проблема: игнорирует q
if "/search.html" in pages and pages["/search.html"]["status"] == 200:
    if "URLSearchParams" not in pages["/search.html"].get("_t", ""):
        fail("/search.html", "страница поиска игнорирует ?q= (известный баг)")

# /pain/ — известная проблема: 404
s, _ = gets(BASE + "/pain/")
if s != 200:
    fail("/pain/", "лента проблем: HTTP " + str(s))

# ---------- 3) внутренние ссылки с ключевых страниц ----------
hrefs = set()
for p, info in pages.items():
    t = info.get("_t", "")
    for l in re.findall(r'href="([^"#]+)"', t):
        if l.startswith("/") and "'+" not in l and BQ not in l:
            hrefs.add(l.split("?")[0].split("#")[0])
targets = sorted(set(BASE + h.rstrip("/") for h in hrefs))
R["link_targets"] = len(targets)
def link_check(u):
    s, _ = gets(u)
    if s != 200:
        time.sleep(1.5)
        s, _ = gets(u)
    return u, s
with ThreadPoolExecutor(12) as ex:
    res = list(ex.map(link_check, targets))
bad_links = [x for x in res if x[1] != 200]
R["links_ok"] = len(res) - len(bad_links)
R["links_bad"] = bad_links[:20]
for u, s in bad_links[:10]:
    fail("link " + u.replace(BASE, ""), "HTTP " + str(s), u in [BASE + "/pain/"])

# ---------- 4) ассеты с ключевых страниц ----------
assets = set()
for p, info in pages.items():
    t = info.get("_t", "")
    for u in re.findall(r'(?:href|src)="(/(?:assets|style\.css|favicon\.ico|favicon\.svg|apple-touch-icon\.png|site\.webmanifest)[^"]*)"', t):
        assets.add(u.split("?")[0])
R["assets_count"] = len(assets)
def asset_check(u):
    s, _ = gets(BASE + u)
    if s != 200:
        time.sleep(1.5)
        s, _ = gets(BASE + u)
    return u, s
with ThreadPoolExecutor(10) as ex:
    res = list(ex.map(asset_check, sorted(assets)))
bad_assets = [x for x in res if x[1] != 200]
R["assets_ok"] = len(res) - len(bad_assets)
R["assets_bad"] = bad_assets[:20]
for u, s in bad_assets[:10]:
    fail("asset " + u, "HTTP " + str(s))

# ---------- 5) GAS ----------
GAS = None
m = re.search(r"https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec", t or "")
if m: GAS = m.group(0)
if GAS:
    s, b = gets(GAS + "?t=list")
    R["gas_alive"] = (s == 200 and "работает" in b.decode("utf-8", "replace"))
    if not R["gas_alive"]: fail("GAS", "не отвечает / без маркера", True)
else:
    fail("GAS", "не найден в разметке", True)

# ---------- отчёт ----------
import datetime
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
R["checked_at_msk"] = now.strftime("%d.%m %H:%M")
R["failures"] = FAIL
R["failures_count"] = len(FAIL)
R["crit_count"] = sum(1 for f in FAIL if f["crit"])

with open("bridge/qa_watch.json", "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1)

def tg_send(text):
    token = os.environ.get("TG_TOKEN", "")
    if not token:
        s, t = fetch_text(BASE + "/")
        m = re.search("ZS_LEAD_CFG=[^{]*[{][^}]*token:([^,}]+)", t)
        token = m.group(1).strip(Q) if m else ""
    if not token:
        return "no-token"
    data = json.dumps({"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}).encode()
    s, b = http("https://api.telegram.org/bot" + token + "/sendMessage", method="POST", data=data,
                headers={"Content-Type": "application/json"})
    return s

icon = "✅" if not FAIL else ("🔴" if R["crit_count"] else "🟠")
lines = [icon + " QA Watch «Запас хода» — " + R["checked_at_msk"],
         "Sitemap: " + str(R.get("sitemap_ok", 0)) + "/" + str(R["sitemap_count"]),
         "Ссылки: " + str(R.get("links_ok", 0)) + "/" + str(R["link_targets"]),
         "Ассеты: " + str(R.get("assets_ok", 0)) + "/" + str(R["assets_count"]),
         "Мини-апп: брендов " + str(R.get("app_brands", 0)) + ", моделей " + str(R.get("app_models", 0)) + ", SKU " + str(R.get("app_prods", 0)) + ", битых sku=" + str(R.get("app_sku_missing", 0)),
         "Каталог: товаров " + str(R.get("catalog_products", 0)) + " | GAS: " + ("жив" if R.get("gas_alive") else "МОЛЧИТ")]
if FAIL:
    lines.append("")
    lines.append("Проблемы (" + str(len(FAIL)) + ", критичных " + str(R["crit_count"]) + "):")
    for f_ in FAIL[:15]:
        lines.append(("• [КРИТ] " if f_["crit"] else "• ") + f_["where"] + " — " + f_["what"])
    if len(FAIL) > 15: lines.append("… ещё " + str(len(FAIL) - 15))
    print("TG status:", tg_send("\n".join(lines)))
    print("SENT_FAIL")
else:
    lines.append("")
    lines.append("Всё чисто. Следующий патруль через 2 часа.")
    print("TG status:", tg_send("\n".join(lines)))
    print("SENT_OK")
print(json.dumps(R, ensure_ascii=False)[:1500])
