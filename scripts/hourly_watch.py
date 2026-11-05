#!/usr/bin/env python3
"""Hourly watch (директива владельца Z-0044): каждый час проверяет прод и пишет отчёт в bridge/hourly_watch.json.
Без ключей. Exit 1 при отказах (заметно в Actions), но отчёт коммитится всегда."""
import json, re, urllib.request, urllib.error, datetime, os, sys

STAMP = str(int(datetime.datetime.utcnow().timestamp()))
BASE = "https://zapashoda-ev.ru"

def get(url):
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + "r=" + STAMP)
    req.add_header("User-Agent", "zapashoda-hourly-watch")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return 0, str(e).encode()

def approx_contains(body, needles):
    text = body.decode("utf-8", "ignore")
    return all(n in text for n in needles), [n for n in needles if n not in text]

results, fails = [], []

def check(name, url, needles=None, not_needles=None, fmt="text"):
    st, body = get(url)
    ok = st == 200 and (body is not None and len(body) > 0)
    detail = ""
    if ok and needles:
        ok2, missing = approx_contains(body, needles)
        ok = ok2 and ok
        if missing: detail = "missing: " + ", ".join(missing[:3])
    if ok and not_needles:
        text_now = body.decode("utf-8", "ignore")
        present = [n for n in not_needles if n in text_now]
        if present:
            ok = False
            detail = "forbidden found: " + ", ".join(present[:3])
    entry = {"check": name, "url": url, "status": st, "ok": ok}
    if detail: entry["detail"] = detail
    results.append(entry)
    if not ok: fails.append(entry)

# базовый прод-смок
check("Главная", f"{BASE}/", needles=["Запас хода"])
check("B2B дилерам", f"{BASE}/b2b/", needles=["Рекомендуемые розничные цены", "Mini App"], not_needles=["1. ЛИДЫ", "300–1 500", "не съедает ваш ФОТ"])
check("Каталог", f"{BASE}/catalog/", needles=["кабель", "адаптер"])
check("Mini App", f"{BASE}/app/", needles=["Запас хода"])
check("Карта станций", f"{BASE}/charging/", needles=["leaflet"])
# модельная страница: берём первый URL из sitemap (не хардкодим slug)
st_sm, body_sm = get(f"{BASE}/sitemap.xml")
model_url = None
if st_sm == 200:
    mmatch = re.search(r"<loc>([^<]*?/models/[^<]*?)</loc>", body_sm.decode("utf-8", "ignore"))
    if mmatch: model_url = mmatch.group(1)
if model_url:
    check("Модельная страница (AEO)", model_url, needles=["Запас хода"])
else:
    results.append({"check": "Модельная страница (AEO)", "url": "sitemap", "status": st_sm, "ok": False, "detail": "no model URL in sitemap"})
    fails.append(results[-1])
# SEO/AEO
check("sitemap.xml", f"{BASE}/sitemap.xml", needles=["<loc>"])
check("robots.txt", f"{BASE}/robots.txt", needles=["Sitemap:", "GPTBot", "PerplexityBot"])
check("llms.txt", f"{BASE}/llms.txt", needles=["Запас хода"])
# мост
st, body = get(f"{BASE}/AI_BRIDGE.json")
bridge_ok = st == 200
bridge_detail = ""
if bridge_ok:
    try:
        bj = json.loads(body)
        bridge_ok = all(k in bj for k in ("last_commit_sha", "last_build_stamp", "open_bugs"))
    except Exception:
        bridge_ok = False
        bridge_detail = "invalid json"
results.append({"check": "AI_BRIDGE.json", "url": f"{BASE}/AI_BRIDGE.json", "status": st, "ok": bridge_ok, "detail": bridge_detail})
if not bridge_ok: fails.append(results[-1])

report = {
    "ts_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "ok": len(fails) == 0,
    "checks_total": len(results),
    "fails": fails,
    "results": results,
}
os.makedirs("bridge", exist_ok=True)
with open("bridge/hourly_watch.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"hourly watch: {len(results)} checks, fails: {len(fails)}")
for r in fails:
    print("  FAIL:", r["check"], r.get("status"), r.get("detail", ""))
sys.exit(1 if fails else 0)
