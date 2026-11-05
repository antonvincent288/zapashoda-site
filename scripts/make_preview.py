#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает самодостаточный офлайн-превью HTML из dist/astro-сборки (wave 9)."""
import json, re, os, base64, mimetypes

DIST = "dist"
OUT = "previews/zapashoda_migration_preview_v2.html"
os.makedirs("previews", exist_ok=True)

PAGES = [
    ("home",      "/",                       "Главная"),
    ("shop",      "/shop/digital/",          "Товары"),
    ("catalog",   "/catalog/",               "Каталог"),
    ("catalog_item", "/catalog/adapter-type2-gbt-premium/", "Товар: адаптер"),
    ("quiz",      "/quiz/",                  "Подбор"),
    ("models",    "/models/",                "Модели"),
    ("model",     "/models/zeekr-001-001-fr/", "Модель"),
    ("blog",      "/blog/",                  "Блог"),
    ("blog_item", "/blog/gbt-stancii-2026/", "Разбор"),
    ("pain",      "/pain/12v-akb/",          "Проблема"),
    ("safety",    "/safety/",                "Безопасность"),
    ("b2b",       "/b2b/",                   "B2B"),
    ("about",     "/about/",                 "О проекте"),
    ("charging",  "/charging/",              "Карта ЗУ"),
]

path_to_id = {p: f"pv_{n}" for n, p, _ in PAGES}

def read_local(rel):
    p = os.path.join(DIST, rel.lstrip("/"))
    return open(p, "rb").read() if os.path.exists(p) else None

def data_uri(rel):
    data = read_local(rel)
    if not data or len(data) > 400_000:
        return None
    ext = os.path.splitext(rel)[1].lower()
    mime = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}.get(ext.lstrip("."), "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

css_all, js_all, seen = [], [], set()

def collect(html):
    for m in re.findall(r'<link rel="stylesheet" href="(/[^"]+\.css)"', html):
        if m not in seen:
            seen.add(m)
            d = read_local(m)
            if d:
                css_all.append(d.decode("utf-8", "replace"))
    for m in re.findall(r'<script[^>]*src="(/[^"]+\.js)"[^>]*></script>', html):
        if m not in seen:
            seen.add(m)
            d = read_local(m)
            if d:
                js_all.append(d.decode("utf-8", "replace"))

def link_rewriter(html):
    def rep(m):
        href = m.group(2)
        if href.startswith("#") or href.startswith("http"):
            return m.group(0)
        if href in path_to_id:
            return f'{m.group(1)}="#{path_to_id[href]}"'
        clean = href.rstrip("/")
        for p, pid in path_to_id.items():
            if clean.rstrip("/") == p.rstrip("/") and not p.endswith(".html"):
                pass
        # файловые ссылки (prod-формат .html)
        alt = clean.replace(".html", "/") if clean.endswith(".html") else None
        if alt and alt in path_to_id:
            return f'{m.group(1)}="#{path_to_id[alt]}"'
        # статические ассеты -> inline
        if re.match(r"^/assets/(sku|og)/.*\.(webp|png|jpg)$", href):
            du = data_uri(href)
            if du:
                return f'{m.group(1)}="{du}"'
        if href.startswith("/assets/leaflet/"):
            return m.group(0)  # обработаем отдельно ниже
        return f'{m.group(1)}="data:,DEAD"'
    return re.sub(r'(href)="([^"]+)"', rep, html)

body_html = []
page_scripts = []
for name, path, label in PAGES:
    fp = os.path.join(DIST, path.lstrip("/"), "index.html")
    if not os.path.exists(fp):
        print("нет страницы:", path)
        continue
    html = open(fp, encoding="utf-8").read()
    collect(html)
    b = html.split("<body", 1)[1].split(">", 1)[1].rsplit("</body>", 1)[0]
    # вшиваем станции для карты
    if name == "charging":
        st = read_local("/charging/stations.json")
        if st:
            page_scripts.append(f"window.__STATIONS_JSON = {st.decode('utf-8')};")
        b = re.sub(r'fetch\((["\'])/charging/stations\.json\1\)',
                   'Promise.resolve(new Response(JSON.stringify(window.__STATIONS_JSON)))', b)
        # leaflet вшиваем
        for asset, tag in [("/assets/leaflet/leaflet.css", "style"), ("/assets/leaflet/markercluster.css", "style"),
                           ("/assets/leaflet/leaflet.js", "script"), ("/assets/leaflet/markercluster.js", "script")]:
            d = read_local(asset)
            if not d:
                continue
            s = d.decode("utf-8", "replace")
            if tag == "style":
                css_all.append(s)
            else:
                page_scripts.append(s)
        b = b.replace('<link rel="stylesheet" href="/assets/leaflet/leaflet.css">', "")
        b = re.sub(r'<link rel="stylesheet" href="/assets/leaflet/markercluster[^"]*">', "", b)
        b = re.sub(r'<script[^>]*src="/assets/leaflet/[^"]*"[^>]*>\s*</script>', "", b)
    b = re.sub(r'<link rel="stylesheet" href="/_astro/[^"]+">', "", b)
    b = re.sub(r'<script[^>]*src="/_astro/[^"]+"[^>]*>\s*</script>', "", b)
    b = link_rewriter(b)
    body_html.append(f'<section class="pv-page" id="pv_{name}" data-label="{label}" style="display:none">{b}</section>')

# шрифт Inter: если в dist есть woff2 — вшиваем
font_face = ""
for root, _, files in os.walk(DIST):
    for f in files:
        if f.endswith(".woff2"):
            fp2 = os.path.join(root, f)
            data = open(fp2, "rb").read()
            if len(data) < 600_000:
                du = f"data:font/woff2;base64,{base64.b64encode(data).decode()}"
                font_face += f"@font-face{{font-family:'Inter';src:url({du}) format('woff2');font-weight:100 900;font-display:swap;}}"
            break

pv_ui = """
.pv-bar{position:fixed;top:0;left:0;right:0;z-index:99999;background:repeating-linear-gradient(45deg,#b45309,#b45309 10px,#92400e 10px,#92400e 20px);color:#fff;font:600 12px/28px system-ui;text-align:center;letter-spacing:.08em}
.pv-nav{position:fixed;bottom:0;left:0;right:0;z-index:99999;background:var(--ink);display:flex;gap:8px;overflow-x:auto;padding:10px 12px;scrollbar-width:none}
.pv-nav::-webkit-scrollbar{display:none}
.pv-nav button{flex:0 0 auto;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);color:#fff;border-radius:999px;padding:7px 14px;font:500 13px system-ui;cursor:pointer;white-space:nowrap}
.pv-nav button.on{background:var(--gold);color:#1d1d1f;border-color:var(--gold);font-weight:700}
.pv-toggle{position:fixed;right:12px;top:40px;z-index:99999;background:#fff;border:1px solid #e5e7eb;border-radius:999px;padding:6px 12px;font:600 13px system-ui;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.08)}
body.pv{padding:28px 0 64px}
.pv-page{display:none!important}
.pv-page.pv-on{display:block!important}
html.dark .pv-toggle{background:#1d1d1f;color:#f5f5f7;border-color:#333}
"""

merged_css = "\n".join(css_all) + font_face + pv_ui
merged_js = "\n".join(js_all)
out = f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Превью миграции v2 — Запас хода (не прод)</title><style>{merged_css}</style></head><body class="pv">
<div class="pv-bar">ПРЕВЬЮ МИГРАЦИИ · НЕ ПРОД · {PAGES.__len__()} страниц · сгенерировано wave9</div>
<button class="pv-toggle" onclick="document.documentElement.classList.toggle('dark')">🌙 Тема</button>
<nav class="pv-nav" id="pv-nav"></nav>
{''.join(body_html)}
<script>{merged_js}</script>
<script>{'\n'.join(page_scripts)}
(function(){{
  var nav = document.getElementById('pv-nav');
  var pages = document.querySelectorAll('.pv-page');
  pages.forEach(function (p) {{
    var b = document.createElement('button');
    b.textContent = p.getAttribute('data-label');
    b.addEventListener('click', function () {{
      pages.forEach(function (x) {{ x.classList.remove('pv-on'); }});
      p.classList.add('pv-on');
      nav.querySelectorAll('button').forEach(function (x) {{ x.classList.remove('on'); }});
      b.classList.add('on');
      window.scrollTo(0, 0);
      var ev = document.createEvent('Event'); ev.initEvent('resize', true, true); window.dispatchEvent(ev);
    }});
    nav.appendChild(b);
  }});
  if (nav.firstChild) nav.firstChild.click();
}})();
</script></body></html>"""

size = len(out.encode())
open(OUT, "w", encoding="utf-8").write(out)
print("OK:", OUT, round(size / 1024), "KB, страниц:", len(body_html))
