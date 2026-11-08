#!/usr/bin/env python3
"""Synthetic shorts v2: многосценовые вертикальные ролики в брендовом стиле.

Вход: data/shorts_scripts.json (сцены: заголовок/подпись, финал с "cta": true).
Рендер: Pillow (кадры) + ffmpeg (сборка, xfade-переходы между сценами).
Выход: assets/shorts/incoming/{slug}.mp4 + {slug}.json — дальше их подхватывает
shorts_ingest.py (по одному за прогон) и публикует в канал и на /shorts/.

Запуск: python scripts/video_generator.py [--one] [--limit N]
Дедуп: по scripts/shorts_published.json (items[].file == slug_zs30.mp4) и по pending в incoming.
"""
import os, json, math, argparse, subprocess, tempfile, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W, H, FPS = 1080, 1920, 20
SCENE_DUR = 3.2
XFADE = 0.5

BG_A = (32, 32, 35)
BG_B = (18, 18, 20)
GOLD = (212, 175, 55)
LIGHT = (229, 229, 234)
MUTED = (110, 110, 116)
FAINT = (142, 142, 147)

def ffmpeg_bin():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

_FONT_CACHE = {}
def font(size):
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    f = None
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/local/share/fonts/DejaVuSans-Bold.ttf",
              os.path.join(ROOT, "assets", "fonts", "DejaVuSans-Bold.ttf"),
              "DejaVuSans-Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf"]:
        if os.path.exists(p):
            f = ImageFont.truetype(p, size); break
    if f is None:
        f = ImageFont.load_default()
    _FONT_CACHE[size] = f
    return f

from PIL import Image, ImageDraw, ImageFont

def gradient_bg():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    steps = 64
    for i in range(steps):
        t = i / (steps - 1)
        c = tuple(int(BG_A[k] + (BG_B[k] - BG_A[k]) * t) for k in range(3))
        d.rectangle([0, H * i // steps, W, H * (i + 1) // steps], fill=c)
    return img

def wrap(d, text, f, maxw):
    words = str(text).split()
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def scene_frame(scene, idx, total, frac, fsizes):
    img = gradient_bg()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=GOLD)
    kicker = "ЗАПАС ХОДА"
    d.text(((W - d.textlength(kicker, font=fsizes['sig'])) / 2, 108), kicker, font=fsizes['sig'], fill=FAINT)
    d.rectangle([W / 2 - 26, 168, W / 2 + 26, 172], fill=GOLD)
    fbig = fsizes['big']
    lines = wrap(d, scene['h'], fbig, W - 160)
    line_h = int(fbig.size * 1.24)
    block_h = len(lines) * line_h
    y0 = 640 - block_h // 2
    for i, ln in enumerate(lines):
        w_ = d.textlength(ln, font=fbig)
        d.text(((W - w_) / 2, y0 + i * line_h), ln, font=fbig, fill=GOLD)
    if scene.get('s'):
        fsub = fsizes['sub']
        slines = wrap(d, scene['s'], fsub, W - 220)
        ys = y0 + block_h + 44
        for i, ln in enumerate(slines):
            w_ = d.textlength(ln, font=fsub)
            d.text(((W - w_) / 2, ys + i * int(fsub.size * 1.3)), ln, font=fsub, fill=LIGHT)
    if scene.get('cta'):
        fcta = fsizes['sub']
        label = "ОТКРЫТЬ ПОДБОР →"
        bw, bh = 640, 122
        x0, y0b = (W - bw) / 2, H - 430
        d.rounded_rectangle([x0, y0b, x0 + bw, y0b + bh], radius=30, outline=GOLD, width=4)
        w_ = d.textlength(label, font=fcta)
        d.text(((W - w_) / 2, y0b + (bh - fcta.size) / 2 - 4), label, font=fcta, fill=GOLD)
    cnt = "%02d / %02d" % (idx + 1, total)
    d.text((W - 210, 108), cnt, font=fsizes['sig'], fill=MUTED)
    bx0, bx1, by = 120, W - 120, H - 190
    d.rounded_rectangle([bx0, by, bx1, by + 10], radius=5, fill=(58, 58, 62))
    fill = bx0 + (bx1 - bx0) * frac
    d.rounded_rectangle([bx0, by, fill, by + 10], radius=5, fill=GOLD)
    foot = "zapashoda-ev.ru"
    d.text(((W - d.textlength(foot, font=fsizes['sig'])) / 2, H - 120), foot, font=fsizes['sig'], fill=MUTED)
    return img

def render_scene(scene, idx, total, tmpdir, tag):
    n = int(FPS * SCENE_DUR)
    fsizes = {'big': font(66), 'sub': font(42), 'sig': font(28)}
    frames_dir = os.path.join(tmpdir, 'f_' + tag)
    os.makedirs(frames_dir, exist_ok=True)
    for k in range(n):
        frac = (idx + k / n) / total
        scene_frame(scene, idx, total, frac, fsizes).save(os.path.join(frames_dir, "f%04d.png" % k))
    out = os.path.join(tmpdir, 'scene_%s.mp4' % tag)
    cmd = [ffmpeg_bin(), "-y", "-framerate", str(FPS), "-i", os.path.join(frames_dir, "f%04d.png"),
           "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", out]
    r = subprocess.run(cmd, capture_output=True, timeout=900)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[-500:])
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    os.rmdir(frames_dir)
    return out

def assemble(scene_files, out_path):
    """xfade-цепочка сцен + тихая аудиодорожка."""
    fb = ffmpeg_bin()
    n = len(scene_files)
    cmd = [fb, "-y"]
    for sf in scene_files:
        cmd += ["-i", sf]
    cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    # индекс lavfi-входа = n
    chains, prev, offset = [], "[0:v]", 0.0
    for i in range(1, n):
        offset += SCENE_DUR - XFADE
        out_v = "[v%d]" % i
        chains.append("%s[%d:v]xfade=transition=fade:duration=%.1f:offset=%.2f%s" % (prev, i, XFADE, offset, out_v))
        prev = out_v
    total_dur = offset + SCENE_DUR
    filt = ";".join(chains)
    cmd += ["-filter_complex", filt,
            "-map", prev, "-map", "%d:a" % n,
            "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-c:a", "aac", "-b:a", "96k",
            "-t", "%.2f" % total_dur, out_path]
    r = subprocess.run(cmd, capture_output=True, timeout=900)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[-600:])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--one', action='store_true', help='сгенерить один шорт за прогон')
    ap.add_argument('--limit', type=int, default=1)
    args = ap.parse_args()
    scripts_path = os.path.join(ROOT, 'data', 'shorts_scripts.json')
    if not os.path.exists(scripts_path):
        print('нет data/shorts_scripts.json — выход'); return
    scripts = json.load(open(scripts_path, encoding='utf-8'))['scripts']
    incoming = os.path.join(ROOT, 'assets', 'shorts', 'incoming')
    os.makedirs(incoming, exist_ok=True)
    published = os.path.join(ROOT, 'scripts', 'shorts_published.json')
    pub = {}
    try:
        pub = json.load(open(published, encoding='utf-8'))
    except Exception:
        pass
    used = {it.get('file') for it in (pub.get('items') or [])}
    limit = 1 if args.one else args.limit
    made = 0
    for sc in scripts:
        slug = sc['id']
        fin = os.path.join(incoming, slug + '.mp4')
        if slug + '_zs30.mp4' in used or os.path.exists(fin):
            continue
        tmp = tempfile.mkdtemp(prefix='zsshorts_')
        try:
            sf = []
            for i, scene in enumerate(sc['scenes']):
                sf.append(render_scene(scene, i, len(sc['scenes']), tmp, str(i)))
            assemble(sf, fin)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        meta = {"title": sc.get('title') or slug, "desc": sc['scenes'][0].get('s') or 'Шорт «Запас хода»',
                "tags": sc.get('tags') or [], "kind": "synthetic", "script_id": slug,
                "no_plate": True}
        json.dump(meta, open(os.path.join(incoming, slug + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('made', fin, os.path.getsize(fin), 'bytes')
        made += 1
        if made >= limit:
            break
    print('done:', made)

if __name__ == '__main__':
    main()
