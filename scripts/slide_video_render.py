#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R-06: рендер настоящих слайд-шортсов (замена synth-заглушек).
Слайд = арт (cover, верх) + антрацит-панель с факт-текстом (низ) + фирменная плашка.
Ken Burns (zoompan) + кроссфейды. Выход по умолчанию: assets/shorts/draft/ (ОБРАЗЕЦ для владельца,
в published попадает только после его «ок» — правило после отката Z-0026).
Запуск: python scripts/slide_video_render.py --out-dir assets/shorts/draft --spec stories/zeekr-moroz"""
import argparse, json, os, subprocess, sys, tempfile, shutil

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
except ImportError:
    print("install: pip install pillow"); sys.exit(0)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1920
ANTHRACITE = (29, 29, 31)
GOLD = (212, 175, 55)
WHITE = (245, 245, 247)
MUT = (142, 142, 147)

def font(name, size):
    p = os.path.join(ROOT, "assets", "fonts", name)
    if not os.path.exists(p):
        p = "/usr/share/fonts/truetype/dejavu/" + name
    return ImageFont.truetype(p, size)

def cover(img, w, h):
    k = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    x = (img.width - w) // 2; y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))

def wrap(draw, text, fnt, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if draw.textlength(t, font=fnt) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines

def make_art_layer(art_path):
    """Арт-слой 1080x1080: cover-кроп, лёгкое затемнение по краям для перехода к панели."""
    if art_path and not os.path.isdir(art_path) and os.path.exists(art_path):
        art = Image.open(art_path).convert("RGB")
        art = cover(art, W, W)
        art = ImageEnhance.Brightness(art).enhance(0.92)
        # нижний градиент-стык к антрациту
        band = Image.new("RGBA", (W, 120), (29, 29, 31, 255))
        grad = Image.new("L", (W, 120))
        gd = ImageDraw.Draw(grad)
        for yy in range(120):
            gd.line([(0, yy), (W, yy)], fill=int(255 * (yy / 119)))
        art.paste(band, (0, W - 120), grad)
        return art
    # без арта — фирменный антрацит с золотой линией
    img = Image.new("RGB", (W, W), ANTHRACITE)
    d = ImageDraw.Draw(img)
    d.rectangle([70, W // 2 - 6, 190, W // 2], fill=GOLD)
    return img


def make_panel(title, sub, footer):
    """Панель 1080x840 (низ кадра): СТАТИЧНАЯ, текст не двигается никогда."""
    H_PANEL = 840
    img = Image.new("RGB", (W, H_PANEL), ANTHRACITE)
    d = ImageDraw.Draw(img)
    d.rectangle([70, 48, 190, 54], fill=GOLD)
    title_f = font("DejaVuSans-Bold.ttf", 64)
    sub_f = font("DejaVuSans.ttf", 42)
    y = 96
    for ln in wrap(d, title, title_f, W - 140):
        d.text((70, y), ln, font=title_f, fill=WHITE); y += 80
    y += 18
    for ln in wrap(d, sub, sub_f, W - 140):
        d.text((70, y), ln, font=sub_f, fill=MUT); y += 56
    f_f = font("DejaVuSans-Bold.ttf", 30)
    d.text((70, H_PANEL - 100), footer, font=f_f, fill=GOLD)
    return img


def render(spec, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    tmp = tempfile.mkdtemp()
    parts = []
    for i, sld in enumerate(spec["slides"]):
        art_png = os.path.join(tmp, f"a{i}.png")
        pan_png = os.path.join(tmp, f"p{i}.png")
        make_art_layer(os.path.join(ROOT, sld["art"]) if sld.get("art") else "").save(art_png)
        make_panel(sld["title"], sld["sub"], spec["footer"]).save(pan_png)
        dur = sld.get("dur", 4.0)
        frames = int(dur * 30)
        # 1) арт: мягкий Ken Burns 1.00 -> 1.06 (только картинка)
        art_m4 = os.path.join(tmp, f"a{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", art_png, "-t", str(dur),
            "-vf", "zoompan=z='min(zoom+0.0005,1.06)':d=%d:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1080:fps=30" % frames,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", art_m4],
            check=True, capture_output=True)
        # 2) панель: статичный поток без фильтров
        pan_m4 = os.path.join(tmp, f"p{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", pan_png, "-t", str(dur),
            "-vf", "fps=30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", pan_m4],
            check=True, capture_output=True)
        # 3) vstack
        sl_m4 = os.path.join(tmp, f"s{i}.mp4")
        subprocess.run(["ffmpeg", "-y", "-i", art_m4, "-i", pan_m4,
            "-filter_complex", "[0:v][1:v]vstack=inputs=2[v]",
            "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", sl_m4],
            check=True, capture_output=True)
        parts.append(sl_m4)
    n = len(parts)
    out = os.path.join(out_dir, spec.get("slug", "slide") + ".mp4")
    if n == 1:
        shutil.copy(parts[0], out)
    else:
        inputs = []
        for pth in parts: inputs += ["-i", pth]
        fc = ""
        for i in range(n - 1):
            a = ("[%d:v]" % i) if i == 0 else ("[v%d]" % (i - 1))
            fc += "%s[%d:v]xfade=transition=fade:duration=0.5:offset=%.2f[v%d];" % (a, i + 1, (i * 3.5) + 3.5, i)
        fc = fc.rstrip(";")
        cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", fc, "-map", "[v%d]" % (n - 2),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", out]
        subprocess.run(cmd, check=True, capture_output=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("rendered:", out, os.path.getsize(out), "bytes")


SPEC = {
  "slug": "slide-01",
  "footer": "ЗАПАС ХОДА · zapashoda-ev.ru",
  "slides": [
    {"art": "assets/img/blog/rasxod-zimoy-bortovoy-kompyuter.webp",
     "title": "EV на морозе теряет 25–40% запаса", "sub": "Это физика, а не поломка. Почему и что с этим делать — за 24 секунды.", "dur": 4.0},
    {"art": "assets/img/blog/vybor-tarifa-dlya-domashnoy-zaryadki.webp",
     "title": "Печка ест 2–4 кВт·ч в час", "sub": "Это 12–25 км хода за час простоя в зимней пробке.", "dur": 4.0},
    {"art": "assets/img/blog/plata-za-prostoy-na-zaryadnyh-stanciyah.webp",
     "title": "Час простоя = 30–120 ₽", "sub": "На быстрой зарядке в городе или на трассе.", "dur": 4.0},
    {"art": "assets/img/blog/bystroaya-zaryadka-kazhdyj-den.webp",
     "title": "Перед DC: прогрей батарею", "sub": "15–20 минут езды — и станция отдаёт полную мощность.", "dur": 4.0},
    {"art": "assets/img/blog/zimnoe-khranenie-elektromobilya-parking-2-4-nedeli.webp",
     "title": "На стоянке: не ниже 20%", "sub": "Глубокий разряд на морозе — главный враг батареи.", "dur": 4.0},
    {"art": "",
     "title": "Проверь свой маршрут", "sub": "Калькулятор «зон смерти»: zapashoda-ev.ru/routes", "dur": 4.0}
  ]
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "assets", "shorts", "draft"))
    ap.add_argument("--spec", default=None, help="путь к JSON-спеке; по умолчанию — встроенный образец")
    ap.add_argument("--slug", default=None)
    a = ap.parse_args()
    spec = SPEC
    if a.spec and os.path.exists(a.spec):
        spec = json.load(open(a.spec, encoding="utf-8"))
    if a.slug: spec["slug"] = a.slug
    render(spec, a.out_dir)
