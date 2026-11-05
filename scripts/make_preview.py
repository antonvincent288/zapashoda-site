#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Офлайн-превью v2.1 из dist: все стили/картинки/leaflet вшиты, module-бандлы убраны."""
import json, re, os, base64

DIST = "dist"
OUT = "previews/zapashoda_migration_preview_v2.html"
os.makedirs("previews", exist_ok=True)

PAGES = [
    ("home",         "/",                                       "Главная"),
    ("shop",         "/shop/digital/",                          "Товары"),
    ("catalog",      "/catalog/",                               "Каталог"),
    ("catalog_item", "/catalog/adapter-type2-gbt-premium.html", "Товар: адаптер"),
    ("quiz",         "/quiz/",                                  "Подбор"),
    ("models",       "/models/",                                "Модели"),
    ("model",        "/models/zeekr-001-001-fr/",               "Модель"),
    ("blog",         "/blog/",                                  "Блог"),
    ("blog_item",    "/blog/gbt-stancii-2026/",                 "Разбор"),
    ("pain",         "/pain/12v-akb/",                          "Проблема"),
    ("safety",       "/safety/",                                "Безопасность"),
    ("b2b",          "/b2b/",                                   "B2B"),
    ("about",        "/about/",                                 "О проекте"),
    ("charging",     "/charging/",                              "Карта ЗУ"),
]
path_to_id = {p: f"pv_{n}" for n, p, _ in PAGES}

def read_local(rel):
    p = os.path.join(DIST, rel.lstrip("/"))
    return open(p, "rb").read() if os.path.exists(p) else None

def data_uri(rel, limit=400_000):
    data = read_local(rel)
    if not data or len(data) > limit:
        return None
    ext = os.path.splitext(rel)[1].lower()
    mime = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "svg": "image/svg+xml", "woff2": "font/woff2"}.get(ext.lstrip("."), "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"

css_all, page_scripts = [], []
seen_css = set()

def collect_css(html):
    for m in re.findall(r'<link[^>]+href="(/[^"]+\.css)"[^>]*>', html):
        if "stylesheet" not in m and 'rel="stylesheet"' not in m:
            continue
    for m in set(re.findall(r'<link[^>]+rel="stylesheet"[^>]*href="([^"]+)"', html)) | set(re.findall(r'<link[^>]+href="(/[^"]+\.css)"[^>]*rel="stylesheet"', html)):
        if m in seen_css:
            continue
        seen_css.add(m)
        d = read_local(m)
        if d:
            css_all.append(d.decode("utf-8", "replace"))

def strip_external_js(html):
    """Убирает module-бандлы и favicon — их нельзя безопасно вшить."""
    html = re.sub(r'<script[^>]*src="/_astro/[^"]+"[^>]*>\s*</script>', "", html)
    html = re.sub(r'<link[^>]+rel="(?:icon|apple-touch-icon|manifest)"[^>]*>', "", html)
    return html

def inline_leaflet(html):
    for m in set(re.findall(r'<link[^>]+href="(/assets/leaflet/[^"]+\.css)"', html)):
        d = read_local(m)
        if d: css_all.append(d.decode("utf-8", "replace"))
        html = re.sub(r'<link[^>]+href="' + re.escape(m) + r'"[^>]*>', "", html)
    for m in set(re.findall(r'<script[^>]*src="(/assets/leaflet/[^"]+\.js)"[^>]*>\s*</script>', html)):
        d = read_local(m)
        if d: page_scripts.append(d.decode("utf-8", "replace"))
        html = re.sub(r'<script[^>]*src="' + re.escape(m) + r'"[^>]*>\s*</script>', "", html)
    return html

def rewrite(html):
    def rep(m):
        attr, url = m.group(1), m.group(2)
        if url.startswith(("#", "http", "data:", "mailto:")):
            return m.group(0)
        if attr == "href":
            if url in path_to_id:
                return f'href="#{path_to_id[url]}"'
            if url.endswith(".html"):
                alt = url[:-5] + "/"
                if alt in path_to_id:
                    return f'href="#{path_to_id[alt]}"'
            return 'href="#'
        if attr == "src":
            du = data_uri(url)
            if du:
                return f'src="{du}"'
            return m.group(0)
        return m.group(0)
    return re.sub(r'\b(href|src)="([^"]+)"', rep, html)

body_html = []
for name, path, label in PAGES:
    fp = os.path.join(DIST, path.lstrip("/"), "index.html")
    if not os.path.exists(fp):
        print("нет страницы:", path)
        continue
    html = open(fp, encoding="utf-8").read()
    collect_css(html)
    html = strip_external_js(html)
    html = inline_leaflet(html)
    if name == "charging":
        st = read_local("/charging/stations.json")
        if st:
            page_scripts.append("window.__STATIONS_JSON = " + st.decode("utf-8", "replace") + ";")
        html = re.sub(r'fetch\((["\'])/charging/stations\.json\1\)',
                      'Promise.resolve(new Response(JSON.stringify(window.__STATIONS_JSON)))', html)
    b = html.split("<body", 1)[1].split(">", 1)[1].rsplit("</body>", 1)[0]
    b = rewrite(b)
    body_html.append(f'<section class="pv-page" id="pv_{name}" data-label="{label}" style="display:none">{b}</section>')

font_face = ""
for root, _, files in os.walk(DIST):
    for f in files:
        if f.endswith(".woff2"):
            fp2 = os.path.join(root, f)
            data = open(fp2, "rb").read()
            if len(data) < 600_000:
                du = f"data:font/woff2;base64,{base64.b64encode(data).decode()}"
                font_face += f"@font-face{{font-family:'Inter';src:url({du}) format('woff2');font-weight:100 900;font-display:swap;}}"

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
out = f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Превью миграции v2.1 — Запас хода (не прод)</title><style>{merged_css}</style></head><body class="pv">
<div class="pv-bar">ПРЕВЬЮ МИГРАЦИИ · НЕ ПРОД · 14 страниц</div>
<button class="pv-toggle" onclick="document.documentElement.classList.toggle('dark')">🌙 Тема</button>
<nav class="pv-nav" id="pv-nav"></nav>
{''.join(body_html)}
<script>{'<\/script><script>'.join(page_scripts)}</script>
<script>
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

open(OUT, "w", encoding="utf-8").write(out)
print("OK:", OUT, round(len(out.encode()) / 1024), "KB, страниц:", len(body_html))
