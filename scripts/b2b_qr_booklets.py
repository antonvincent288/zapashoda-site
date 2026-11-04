#!/usr/bin/env python3
# Z-0021: генерация персональных PDF-буклетов с QR-кодами для дилеров.
# Вход: data/b2b_partners_seed.json  = ["ID_001", "ID_002", ...] (выгрузка из CRM владельца)
# Выход: assets/b2b/booklets/b2b_booklet_<ID>.pdf + assets/b2b/booklets/index.json
# Каждый PDF: обложка «Запас хода», персональная ссылка /b2b/onboarding/?start=<ID>, QR.
import json, os, sys

try:
    import qrcode
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except ImportError:
    print("install: pip install qrcode reportlab"); sys.exit(0)

BASE = "https://zapashoda-ev.ru/b2b/onboarding/"

def main():
    seed_path = "data/b2b_partners_seed.json"
    if not os.path.exists(seed_path):
        print("нет data/b2b_partners_seed.json — жду выгрузку из CRM владельца (Z-0021 standby)")
        return
    ids = json.load(open(seed_path, encoding="utf-8"))
    if not isinstance(ids, list) or not ids:
        print("seed пуст — пропускаю"); return
    outdir = "assets/b2b/booklets"
    os.makedirs(outdir, exist_ok=True)
    manifest = []
    for pid in ids:
        pid = str(pid).strip()
        if not pid: continue
        link = BASE + "?start=" + pid
        img_path = os.path.join(outdir, f"qr_{pid}.png")
        qr = qrcode.QRCode(border=2, box_size=10)
        qr.add_data(link); qr.make(fit=True)
        qr.make_image(fill_color="#1d1d1f", back_color="white").save(img_path)
        pdf_path = os.path.join(outdir, f"b2b_booklet_{pid}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        w, h = A4
        c.setFillColorRGB(0.114, 0.114, 0.122); c.rect(0, 0, w, h, fill=1, stroke=0)
        c.setFillColorRGB(0.83, 0.686, 0.216)  # золото #D4AF37
        c.setFont("Helvetica-Bold", 26); c.drawCentredString(w/2, h-120, "ZAPAS KHODA")
        c.setFont("Helvetica", 15); c.setFillColorRGB(1, 1, 1)
        c.drawCentredString(w/2, h-160, "Partnership Booklet - " + pid)
        c.setFont("Helvetica", 12)
        c.drawCentredString(w/2, h-200, "Scan to connect: personal onboarding link")
        c.drawImage(img_path, w/2-150, h-560, width=300, height=300)
        c.setFillColorRGB(0.7, 0.7, 0.7); c.setFont("Helvetica", 9)
        c.drawCentredString(w/2, 80, link)
        c.save()
        manifest.append({"id": pid, "link": link, "pdf": f"/assets/b2b/booklets/b2b_booklet_{pid}.pdf"})
        print("ok:", pid)
    json.dump({"generated": time.strftime("%Y-%m-%dT%H:%M:%S+03:00"), "count": len(manifest), "booklets": manifest},
              open(os.path.join(outdir, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("booklets:", len(manifest))

import time
if __name__ == "__main__":
    main()
