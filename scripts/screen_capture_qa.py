#!/usr/bin/env python3
"""R-06 (дополнение): скринкасты ключевых страниц → вертикальный MP4.

Метод: Playwright (Chromium headless) — открытие страницы, автоскролл,
серия JPEG-кадров → наложение плашки «ЗАПАС ХОДА» (VISUAL_SPEC: антрацит+
золото) → MP4 (ffmpeg из imageio-ffmpeg). Записи пишутся в data/shorts.json,
/shorts/ и video-sitemap обновляются при следующей сборке.

Установка (если Playwright ещё не стоит): pip install playwright && playwright install chromium
Запуск: python scripts/screen_capture_qa.py [--pages calculator,routes] [--frames 30]
Если в системе есть chromium, скрипт использует его (флаги --single-process).
"""
import os, json, io, subprocess, tempfile, argparse, shutil
from datetime import date
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def ffmpeg_bin():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def plaque(jpeg_bytes):
    img = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
    W, H = img.size
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 86], fill="#1d1d1f")
    d.rectangle([0, 86, W, 92], fill="#D4AF37")
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
    except Exception:
        f = ImageFont.load_default()
    t = "ЗАПАС ХОДА"
    d.text(((W - d.textlength(t, font=f)) / 2, 20), t, font=f, fill="#D4AF37")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return buf.getvalue()

def shoot(url, n_frames, out_dir):
    from playwright.sync_api import sync_playwright
    ok = False
    with sync_playwright() as p:
        args = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-crash-reporter"]
        exe = shutil.which("chromium") or shutil.which("google-chrome")
        if exe:
            args.append("--single-process")
        browser = p.chromium.launch(executable_path=exe, args=args) if exe else p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        for i in range(n_frames):
            try:
                page.screenshot(path=os.path.join(out_dir, "f%04d.jpg" % i), type="jpeg", quality=72)
            except Exception as e:
                print("frame skip", i, repr(e)[:80]); continue
            try:
                page.mouse.wheel(0, 520 if i % 2 == 0 else 340)
            except Exception:
                pass
            page.wait_for_timeout(280)
        browser.close()
        ok = len(os.listdir(out_dir)) > 0
    return ok

PAGES = {
    "calculator": {"url": "https://zapashoda-ev.ru/calculator/", "title": "Калькулятор: стоимость зарядки и цена простоя", "desc": "Считаем 100 км по домашнему, городскому и трассовому тарифу — и цену простоя."},
    "routes": {"url": "https://zapashoda-ev.ru/routes/", "title": "Имперский маршрут: зоны смерти трасс", "desc": "Проверьте, где на М-4, М-11 и М-12 между зарядками больше, чем ваш запас."},
    "telemetry": {"url": "https://zapashoda-ev.ru/telemetry/", "title": "Стресс-тест батарей РФ", "desc": "Публичный дашборд телеметрии: SOH по регионам и моделям."},
}

def to_mp4(frames_dir, out_path, fps=8):
    fb = ffmpeg_bin()
    cmd = [fb, "-y", "-framerate", str(fps), "-i", os.path.join(frames_dir, "f%04d.jpg"),
           "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
           "-movflags", "+faststart", out_path]
    r = subprocess.run(cmd, capture_output=True, timeout=600)
    return r.returncode == 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pages', default='calculator,routes')
    ap.add_argument('--frames', type=int, default=30)
    ap.add_argument('--out', default=os.path.join(ROOT, 'assets', 'shorts', 'published'))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    data_path = os.path.join(ROOT, 'data', 'shorts.json')
    data = json.load(open(data_path, encoding='utf-8')) if os.path.exists(data_path) else {'shorts': []}
    have = {s.get('file') for s in data.get('shorts', [])}
    made = 0
    for key in args.pages.split(','):
        meta = PAGES.get(key.strip())
        if not meta:
            print('unknown page', key); continue
        tmp = tempfile.mkdtemp(prefix='zscastf_')
        print('shooting', key)
        try:
            ok = shoot(meta['url'], args.frames, tmp)
        except Exception as e:
            print('shoot fail:', repr(e)[:200]); ok = False
        if not ok:
            shutil.rmtree(tmp, ignore_errors=True); continue
        files = sorted(os.listdir(tmp))
        good = []
        for f in files:
            try:
                open(os.path.join(tmp, f), 'wb').write(plaque(open(os.path.join(tmp, f), 'rb').read()))
                good.append(f)
            except Exception as e:
                print('frame bad', f, repr(e)[:60])
                os.remove(os.path.join(tmp, f))
        fname = 'screencast-%s.mp4' % key
        outp = os.path.join(args.out, fname)
        ok = to_mp4(tmp, outp, fps=8)
        shutil.rmtree(tmp, ignore_errors=True)
        if not ok:
            print('ffmpeg fail', key); continue
        if fname not in have:
            data.setdefault('shorts', []).append({'file': fname, 'title': meta['title'],
                'desc': meta['desc'], 'url': '/assets/shorts/published/' + fname,
                'added': date.today().isoformat(), 'kind': 'screencast'})
            made += 1
        print('made', outp, os.path.getsize(outp))
    if made:
        data['updated'] = date.today().isoformat()
        json.dump(data, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('done:', made)

if __name__ == '__main__':
    main()
