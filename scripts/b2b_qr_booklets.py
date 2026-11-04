#!/usr/bin/env python3
# Z-0021: генерация персональных PDF-буклетов с QR-кодами для дилеров.
# Вход: data/b2b_partners_seed.json — либо список строк ["ID_001", ...],
#       либо {"partners": [{id, name, brand, city, address, phone, ...}]}
# Выход: assets/b2b/booklets/b2b_booklet_<ID>.pdf + assets/b2b/booklets/index.json
# Дизайн: антрацит/золото, кириллица (DejaVuSans), без иллюстраций (правило визуалов 04.11).
import json, os, sys, time

try:
    import qrcode
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("install: pip install qrcode reportlab"); sys.exit(0)

BASE = "https://zapashoda-ev.ru/b2b/onboarding/"
GOLD = (0.83, 0.686, 0.216)
INK = (0.114, 0.114, 0.122)

def load_partners(seed_path):
    data = json.load(open(seed_path, encoding="utf-8"))
    if isinstance(data, dict) and data.get("partners"):
        return data["partners"]
    if isinstance(data, list):
        return [{"id": str(x).strip()} for x in data if str(x).strip()]
    return []

def draw_booklet(pdf_path, qr_path, partner):
    w, h = A4
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setFillColorRGB(*INK); c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setStrokeColorRGB(*GOLD); c.setLineWidth(2); c.rect(28, 28, w-56, h-56)
    c.setFillColorRGB(*GOLD); c.setFont("DejaVuSans-Bold", 30)
    c.drawCentredString(w/2, h-110, "ЗАПАС ХОДА")
    c.setFillColorRGB(1, 1, 1); c.setFont("DejaVuSans", 13)
    c.drawCentredString(w/2, h-140, "Зарядное оборудование для автосалонов")
    c.setStrokeColorRGB(*GOLD); c.setLineWidth(0.8); c.line(120, h-155, w-120, h-155)
    name = partner.get("name", partner.get("id", ""))
    c.setFont("DejaVuSans-Bold", 15); c.drawCentredString(w/2, h-210, "Ваша персональная точка входа")
    c.setFont("DejaVuSans", 12); c.setFillColorRGB(0.85, 0.85, 0.85)
    c.drawCentredString(w/2, h-232, name[:60])
    c.setFillColorRGB(*GOLD); c.setFont("DejaVuSans-Bold", 13)
    c.drawCentredString(w/2, h-256, partner.get("id", ""))
    lines = [
        "Правильная зарядка под каждую модель клиента —",
        "145 моделей в нашей базе, совместимость проверена.",
        "",
        "Готовый скрипт и материалы: менеджер продаёт,",
        "не разбираясь в технике.",
        "",
        "Матрица заработка: маржа салона с одной машины —",
        "3-15 тыс. ₽ (оценка до сверки прайс-листа).",
    ]
    y = h - 330
    for ln in lines:
        c.setFillColorRGB(0.92, 0.92, 0.92) if ln else c.setFillColorRGB(*INK)
        if ln:
            c.setFont("DejaVuSans", 11.5); c.drawCentredString(w/2, y, ln)
        y -= 18
    c.drawImage(qr_path, w/2-140, 320, width=280, height=280)
    link = BASE + "?start=" + partner.get("id", "")
    c.setFillColorRGB(0.55, 0.55, 0.55); c.setFont("DejaVuSans", 8.5)
    c.drawCentredString(w/2, 295, link)
    c.setFillColorRGB(*GOLD); c.setFont("DejaVuSans-Bold", 11)
    c.drawCentredString(w/2, 120, "Сканируйте — доступ к закрытому B2B-кабинету")
    c.drawCentredString(w/2, 100, "придёт в Telegram в течение рабочего дня")
    c.setFillColorRGB(0.45, 0.45, 0.45); c.setFont("DejaVuSans", 8)
    c.drawCentredString(w/2, 55, "zapashoda-ev.ru · поставки адаптеров, кабелей и зарядных станций для EV и PHEV")
    c.save()

def main():
    seed_path = "data/b2b_partners_seed.json"
    if not os.path.exists(seed_path):
        print("нет data/b2b_partners_seed.json — жду seed (Z-0021 standby)")
        return
    partners = load_partners(seed_path)
    if not partners:
        print("seed пуст — пропускаю"); return
    outdir = "assets/b2b/booklets"
    os.makedirs(outdir, exist_ok=True)
    for fp, fname in [("assets/fonts/DejaVuSans.ttf", "DejaVuSans"),
                      ("assets/fonts/DejaVuSans-Bold.ttf", "DejaVuSans-Bold")]:
        if not os.path.exists(fp):
            print("нет шрифта:", fp, "— кириллица невозможна"); return
        pdfmetrics.registerFont(TTFont(fname, fp))
    manifest = []
    for partner in partners:
        pid = str(partner.get("id", "")).strip()
        if not pid: continue
        link = BASE + "?start=" + pid
        qr_img = os.path.join(outdir, f"qr_{pid}.png")
        qr = qrcode.QRCode(border=2, box_size=12)
        qr.add_data(link); qr.make(fit=True)
        qr.make_image(fill_color="#1d1d1f", back_color="white").save(qr_img)
        pdf_path = os.path.join(outdir, f"b2b_booklet_{pid}.pdf")
        draw_booklet(pdf_path, qr_img, partner)
        os.remove(qr_img)
        manifest.append({"id": pid, "name": partner.get("name", ""), "priority": partner.get("priority", ""),
                         "negotiations": partner.get("negotiations", ""),
                         "link": link, "pdf": f"/assets/b2b/booklets/b2b_booklet_{pid}.pdf"})
        print("ok:", pid)
    json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%S+03:00"), "count": len(manifest),
               "booklets": manifest},
              open(os.path.join(outdir, "index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("booklets:", len(manifest))

if __name__ == "__main__":
    main()
