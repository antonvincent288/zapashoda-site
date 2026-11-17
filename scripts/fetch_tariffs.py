#!/usr/bin/env python3
"""Автообновление тарифов ЭЗС из открытых источников операторов.

Запускается по расписанию GitHub Actions (ежедневно). Результат:
site/public/tariffs.json — его читает дашборд /dashboard/.

Принципы:
- Официальные сайты операторов; никаких выдуманных значений.
- Если источник не отдал данные, прежние значения в json сохраняются,
  у сети ставится status: parse_failed и last_check.
- Двойная загрузка (urllib, затем curl): берём первый вариант, где
  найдены цены.
"""
import json, re, subprocess, sys, datetime, os

SOURCES = [
    {"network": "Энергия Москвы", "url": "https://evacharge.me/", "patterns": [
        (r"Медленн.{0,80}?(\d{1,2}(?:[.,]\d{1,2})?)\s*руб\s*/\s*кВт", "ac"),
        (r"Быстры.{0,80}?(\d{1,2}(?:[.,]\d{1,2})?)\s*руб\s*/\s*кВт", "dc"),
    ]},
    {"network": "РусГидро", "url": "https://charge.rushydro.ru/electrocar/", "patterns": [
        (r"(\d{1,2}(?:[.,]\d{1,2})?)\s*руб\.\s*за\s*1\s*кВт\*?ч\s*на\s*медленной", "ac"),
        (r"(\d{1,2}(?:[.,]\d{1,2})?)\s*руб\.\s*за\s*1\s*кВт\*?ч\s*на\s*быстрой", "dc"),
    ]},
]

UA = "zapashoda-tariffs/1.0 (+https://zapashoda-ev.ru)"

def http_get_variants(url):
    variants = []
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            variants.append(r.read().decode("utf-8", "ignore"))
    except Exception:
        pass
    try:
        out = subprocess.run(["curl", "-s", "-L", "-A", UA, url],
                             capture_output=True, timeout=45)
        variants.append(out.stdout.decode("utf-8", "ignore"))
    except Exception:
        pass
    return variants

def strip_html(s):
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def parse(html_text, patterns):
    text = strip_html(html_text)
    res = {}
    for pat, kind in patterns:
        m = re.search(pat, text)
        if m:
            res[kind] = float(m.group(1).replace(",", "."))
    return res

def main():
    path = "site/public/tariffs.json"
    data = {"networks": {}, "market": {"dc_typical": [17, 26],
            "note": "коридор цен по открытым обзорам рынка"}, "sources": []}
    if os.path.exists(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
            data.setdefault("networks", {})
        except Exception:
            pass
    now = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")
    ok_any = False
    for src in SOURCES:
        vals = {}
        for html_text in http_get_variants(src["url"]):
            if not html_text:
                continue
            vals = parse(html_text, src["patterns"])
            if vals:
                break
        net = data["networks"].setdefault(src["network"], {})
        if vals:
            ok_any = True
            net.update(vals)
            net["unit"] = "₽/кВт·ч"
            net["source"] = src["url"]
            net["updated"] = now
            net["status"] = "parsed"
        else:
            net["status"] = "parse_failed"
            net.setdefault("source", src["url"])
            net["last_check"] = now
        print(src["network"], "->", {k: net.get(k) for k in ("ac", "dc", "status")})
    data["updated"] = now
    data["sources"] = [s["url"] for s in SOURCES]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if not ok_any:
        print("WARNING: ни один источник не распарсен — значения в json не обновлены")

if __name__ == "__main__":
    main()
