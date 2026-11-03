#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборщик премиум-PDF гайдов по VISUAL_SPEC (вечный регламент владельца 03.11):
чередование фонов разделов антрацит #1d1d1f / светлый #f5f5f7, золотые закруглённые
боксы болей/лайфхаков #D4AF37, ноль заглушек. Вход — bridge/drafts/guides/approved/
(проверено Арт-Директором). Выход — static/products/<slug>.pdf + включение продукта
в data/shop_products.json (live=true)."""
import json, os, re, sys, html as _html
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _font(name):
    p = os.path.join(ROOT, "assets", "fonts", name)
    return p if os.path.exists(p) else "/usr/share/fonts/truetype/dejavu/" + name
pdfmetrics.registerFont(TTFont("DejaVu", _font("DejaVuSans.ttf")))
try: pdfmetrics.registerFont(TTFont("DejaVu-Bold", _font("DejaVuSans-Bold.ttf")))
except Exception: pdfmetrics.setFontRegistrationCallback and None; pass
ANTHRACITE = (0.114, 0.114, 0.122)
LIGHT = (0.961, 0.961, 0.969)
GOLD = (0.831, 0.686, 0.216)
GOLDBG_DARK = (0.16, 0.15, 0.10)
GOLDBG_LIGHT = (0.933, 0.886, 0.745)
WHITE = (1, 1, 1)
DARKTXT = (0.114, 0.114, 0.122)
MUT = (0.43, 0.43, 0.45)
def strip_tags(s): return _html.unescape(re.sub(r"<[^>]+>", " ", s))
def parse_chapter(ch):
    out = []
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>|<div class=[\"']gbox[\"'][^>]*>(.*?)</div>|<li[^>]*>(.*?)</li>|<p[^>]*>(.*?)</p>", ch, re.S):
        if m.group(1): out.append(("h2", strip_tags(m.group(1)).strip()))
        elif m.group(2):
            lbl = re.search(r"<b>([^<]*)</b>", m.group(2))
            out.append(("gbox", (lbl.group(1) if lbl else "Боль"), strip_tags(m.group(2)).strip()))
        elif m.group(3): out.append(("li", strip_tags(m.group(3)).strip()))
        elif m.group(4): out.append(("p", strip_tags(m.group(4)).strip()))
    return out
def wrap(c, text, font, size, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines or [""]
def render(slug, guide):
    out = os.path.join(ROOT, "static", "products", slug + ".pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    c = canvas.Canvas(out, pagesize=A4)
    W, H = A4; M = 46
    def page(bg):
        c.setFillColorRGB(*bg); c.rect(0, 0, W, H, stroke=0, fill=1)
        c.setFont("DejaVu", 8)
        c.setFillColorRGB(*(MUT if bg == LIGHT else (0.62, 0.64, 0.62)))
        c.drawString(M, 24, "Запас Хода · zapashoda-ev.ru · персональная копия")
        c.drawRightString(W - M, 24, "Платный гайд · копирование запрещено")
    def title_lines(text, font, size, col, x, y, lh):
        c.setFont(font, size); c.setFillColorRGB(*col)
        for ln in wrap(c, text, font, size, W - 2 * M):
            c.drawString(x, y, ln); y -= lh
        return y
    # обложка: антрацит + золото
    page(ANTHRACITE)
    c.setFont("DejaVu-Bold", 15); c.setFillColorRGB(*GOLD)
    c.drawString(M, H - 88, "ЗАПАС ХОДА")
    c.setStrokeColorRGB(*GOLD); c.setLineWidth(2); c.line(M, H - 98, M + 118, H - 98)
    y = title_lines(guide.get("title", ""), "DejaVu-Bold", 28, WHITE, M, H - 170, 36)
    y = title_lines(guide.get("desc", ""), "DejaVu", 13, (0.7, 0.73, 0.7), M, y - 26, 19)
    chs = [ch for ch in guide.get("chapters", []) if ch]
    c.setFont("DejaVu-Bold", 13); c.setFillColorRGB(*GOLD)
    c.drawString(M, H - 330, "СОДЕРЖАНИЕ · %d РАЗДЕЛОВ" % len(chs))
    yy = H - 358
    for i, ch in enumerate(chs, 1):
        h2s = re.search(r"<h2[^>]*>(.*?)</h2>", ch, re.S)
        t = strip_tags(h2s.group(1)).strip() if h2s else "Раздел %d" % i
        c.setFillColorRGB(*WHITE); c.setFont("DejaVu", 12)
        for ln in wrap(c, "%d. %s" % (i, t), "DejaVu", 12, W - 2 * M - 18):
            c.drawString(M + 14, yy, ln); yy -= 17
        yy -= 6
    c.showPage()
    for idx, ch in enumerate(chs):
        dark = (idx % 2 == 0)
        bg = ANTHRACITE if dark else LIGHT
        col = WHITE if dark else DARKTXT
        page(bg)
        y = H - 76
        for kind, *rest in parse_chapter(ch):
            if kind == "h2":
                y -= 12
                if y < 120: page(bg); y = H - 76
                y = title_lines(rest[0], "DejaVu-Bold", 16.5, col, M, y, 22) - 8
            elif kind == "p":
                for ln in wrap(c, rest[0], "DejaVu", 11.5, W - 2 * M):
                    if y < 92: page(bg); y = H - 76
                    c.setFont("DejaVu", 11.5); c.setFillColorRGB(*col)
                    c.drawString(M, y, ln); y -= 17
                y -= 6
            elif kind == "li":
                for ln in wrap(c, "•  " + rest[0], "DejaVu", 11.5, W - 2 * M - 14):
                    if y < 92: page(bg); y = H - 76
                    c.setFont("DejaVu", 11.5); c.setFillColorRGB(*col)
                    c.drawString(M + 12, y, ln); y -= 17
                y -= 3
            elif kind == "gbox":
                label, body = rest
                lines = wrap(c, body, "DejaVu", 11, W - 2 * M - 34)
                h = 36 + len(lines) * 15
                if y - h < 92: page(bg); y = H - 76
                c.setFillColorRGB(*(GOLDBG_DARK if dark else GOLDBG_LIGHT))
                c.roundRect(M - 4, y - h, W - 2 * M + 8, h, 12, stroke=0, fill=1)
                c.setStrokeColorRGB(*GOLD); c.setLineWidth(2)
                c.roundRect(M - 4, y - h, W - 2 * M + 8, h, 12, stroke=1, fill=0)
                c.setFont("DejaVu-Bold", 10); c.setFillColorRGB(*GOLD)
                c.drawString(M + 12, y - 17, label.upper())
                c.setFont("DejaVu", 11); c.setFillColorRGB(*DARKTXT)
                ty = y - 34
                for ln in lines:
                    c.drawString(M + 12, ty, ln); ty -= 15
                y = y - h - 12
        c.showPage()
    c.save()
    return out
def load_prod():
    p = os.path.join(ROOT, "data", "shop_products.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"products": []}
def gas_pdfs():
    """Список продуктов, PDF которых зарегистрированы в GAS (Drive). None — GAS недоступен."""
    import json as _json, urllib.request, urllib.error
    cfgp = os.path.join(ROOT, "data", "site_config.json")
    try: cfg = _json.load(open(cfgp, encoding="utf-8"))
    except Exception: return None
    gas = str((cfg.get("shop") or {}).get("gas_pay_url") or cfg.get("gas_pay_url") or "")
    if not gas: return None
    try:
        r = urllib.request.Request(gas, data=_json.dumps({"t": "bonus_selftest"}).encode(),
                                   headers={"Content-Type": "text/plain;charset=utf-8"})
        resp = _json.loads(urllib.request.urlopen(r, timeout=25).read().decode("utf-8", errors="replace"))
        return list(resp.get("pdfs") or []) if resp.get("ok") else None
    except Exception:
        return None
def main():
    appr = os.path.join(ROOT, "bridge", "drafts", "guides", "approved")
    if not os.path.isdir(appr): print("approved пуст"); return
    prod = load_prod()
    built = []
    registered = gas_pdfs()
    print("GAS pdfs:", registered)
    for fn in sorted(os.listdir(appr)):
        if not fn.endswith(".json"): continue
        slug = fn[:-5]
        d = json.load(open(os.path.join(appr, fn), encoding="utf-8"))
        if d.get("qa_failed"): print(slug, ": qa_failed — пропуск"); continue
        if len([x for x in d.get("chapters", []) if x]) < 6: print(slug, ": глав <6 — пропуск"); continue
        try:
            render(slug, d)
            built.append(slug)
            # Live ТОЛЬКО если PDF зарегистрирован в GAS (Drive) — иначе покупка без файла невозможна
            if registered and slug in registered:
                for pp in prod["products"]:
                    if pp.get("slug") == slug: pp["live"] = True
                print(slug, ": live (PDF зарегистрирован в GAS)")
            else:
                print(slug, ": PDF собран, но не зарегистрирован в GAS — статус «скоро» остаётся")
        except Exception as e:
            print("PDF fail", slug, repr(e))
    if built:
        json.dump(prod, open(os.path.join(ROOT, "data", "shop_products.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("собраны PDF:", ", ".join(built))
    else:
        print("новых PDF нет")
if __name__ == "__main__":
    main()
