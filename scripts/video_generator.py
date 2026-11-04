#!/usr/bin/env python3
"""R-06 SYNTHETIC: генератор вертикальных MP4-роликов без регистрации.

Метод: Pillow рисует кадры (фон #1d1d1f антрацит, пульсирующий текст #D4AF37
золото), ffmpeg (бинарник из imageio-ffmpeg, без внешних установок) собирает MP4.
Заголовки — из data/blog_extra/*.json (+ встроенный список болей).
Выход: assets/shorts/published/*.mp4 + data/shorts.json (страница /shorts/
и JSON-LD VideoObject на главной собираются из неё при следующей сборке).

Запуск: python scripts/video_generator.py [--limit 12] [--out assets/shorts/published]
"""
import os, json, glob, math, argparse, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def ffmpeg_bin():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(draw, text, font, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def draw_frame(lines, sub, pulse, W, H, fbig, fsub, fsig):
    img = Image.new("RGB", (W, H), "#1d1d1f")
    d = ImageDraw.Draw(img)
    # тонкая золотая рамка-бар
    d.rectangle([0, 0, W, 8], fill="#D4AF37")
    # подпись «запас хода» сверху
    d.text(((W - d.textlength("ЗАПАС ХОДА", font=fsig)) / 2, 46), "ЗАПАС ХОДА", font=fsig, fill="#8e8e93")
    # пульсирующий заголовок: масштаб через межстрочные сдвиги (дешёво и стабильно)
    line_h = int(fbig.size * 1.22)
    block_h = len(lines) * line_h
    y0 = (H - block_h) // 2 + int(math.sin(pulse) * 8)
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=fbig)
        d.text(((W - w) / 2, y0 + i * line_h), ln, font=fbig, fill="#D4AF37")
    if sub:
        ysub = y0 + block_h + 26
        d.text(((W - d.textlength(sub, font=fsub)) / 2, ysub), sub, font=fsub, fill="#e5e5ea")
    d.text(((W - d.textlength("zapashoda-ev.ru", font=fsig)) / 2, H - 60), "zapashoda-ev.ru", font=fsig, fill="#48484a")
    return img

def render_mp4(frames_dir, out_path, fps):
    fb = ffmpeg_bin()
    cmd = [fb, "-y", "-framerate", str(fps), "-i", os.path.join(frames_dir, "f%04d.png"),
           "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
           "-movflags", "+faststart", out_path]
    r = subprocess.run(cmd, capture_output=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[-400:])

def topics():
    t = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'blog_extra', '*.json'))):
        try:
            j = json.load(open(f, encoding='utf-8'))
            t.append((j.get('title') or '', j.get('slug') or ''))
        except Exception:
            pass
    fixed = [
        ("Ночная зарядка: 3-4 руб. за кВт-ч", "Дом ночью — самое дешёвое «топливо»"),
        ("Зимой расход растёт на 20-40%", "Планируйте по реальному расходу"),
        ("Быстрая станция: 15-25 руб. за кВт-ч", "Городские DC-сети"),
        ("После 80% скорость падает", "Не платите за медленный поток"),
        ("Потери при зарядке: 5-10%", "Учитывайте «обогрев улицы»"),
        ("Гайд «Цифровой Штурман» — 990 руб.", "Зарядная инфраструктура трассы под рукой"),
    ]
    for title, sub in fixed:
        t.append((title, ""))
    return t

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=12)
    ap.add_argument('--out', default=os.path.join(ROOT, 'assets', 'shorts', 'published'))
    ap.add_argument('--keep-frames', action='store_true')
    args = ap.parse_args()
    W, H, FPS, DUR = 720, 1280, 24, 1.5
    n_frames = int(FPS * DUR)
    fbig, fsub, fsig = font(46), font(30), font(26)
    os.makedirs(args.out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='zsframes_')
    os.makedirs(tmp, exist_ok=True)
    data_path = os.path.join(ROOT, 'data', 'shorts.json')
    data = json.load(open(data_path, encoding='utf-8')) if os.path.exists(data_path) else {'shorts': []}
    have = {s.get('file') for s in data.get('shorts', [])}
    made = []
    for i, (title, sub) in enumerate(topics()[:args.limit]):
        slug = 'synth-%02d' % (i + 1)
        fname = slug + '.mp4'
        if fname in have:
            print('skip', fname); continue
        lines = wrap(ImageDraw.Draw(Image.new("RGB", (10, 10))), title, fbig, W - 80)
        for k in range(n_frames):
            img = draw_frame(lines, sub, 2 * math.pi * k / n_frames, W, H, fbig, fsub, fsig)
            img.save(os.path.join(tmp, 'f%04d.png' % k))
        out_path = os.path.join(args.out, fname)
        render_mp4(tmp, out_path, FPS)
        rec = {'file': fname, 'title': title, 'desc': sub or 'Факт по зарядке EV в России',
               'url': '/assets/shorts/published/' + fname,
               'added': __import__('datetime').date.today().isoformat(), 'kind': 'synthetic'}
        data.setdefault('shorts', []).append(rec)
        have.add(fname)
        made.append(fname)
        print('made', fname, os.path.getsize(out_path), 'bytes')
    # дедуп по файлу
    seen = set(); uniq = []
    for s in data['shorts']:
        if s.get('file') in seen: continue
        seen.add(s.get('file')); uniq.append(s)
    data['shorts'] = uniq[-40:]
    data['updated'] = __import__('datetime').date.today().isoformat()
    json.dump(data, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if not args.keep_frames:
        for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
    print('done:', len(made))

if __name__ == '__main__':
    main()
