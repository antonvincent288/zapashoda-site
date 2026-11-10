#!/usr/bin/env python3
"""Conveyor helper: validate + publish one article to astrowind-migration.

Usage:
  export GIT_TOKEN=github_pat_...
  python tools/conveyor/make_article.py --json article.json --og-title "..." [--og-cat "Категория"] [--check-only]

article.json fields: slug, title, desc, category, read_min, date, og, body_html, faq (list, no ruble signs).
Rules enforced: slug free, >=8 internal links, 500-950 words, no ruble in FAQ, no latin-dot-cyr, all internal links resolve.
"""
import re, json, sys, io, base64, tarfile, time, argparse, urllib.request, urllib.error

REPO = 'antonvincent288/zapashoda-site'
BRANCH = 'astrowind-migration'
API = f'https://api.github.com/repos/{REPO}'

def req(url, method='GET', payload=None, token=None, tries=3):
    for i in range(tries):
        data = json.dumps(payload).encode() if payload is not None else None
        r = urllib.request.Request(url, data=data, method=method)
        r.add_header('Authorization', 'Bearer ' + token)
        if data: r.add_header('Content-Type', 'application/json')
        r.add_header('User-Agent', 'conveyor-helper')
        try:
            return json.loads(urllib.request.urlopen(r, timeout=120).read())
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'ignore')[:300]
            if e.code in (403, 502) and i < tries - 1:
                time.sleep(10); continue
            print(f'HTTPERR {e.code}: {body}', file=sys.stderr); return None
        except Exception as e:
            if i < tries - 1: time.sleep(10); continue
            print(f'ERR {e}', file=sys.stderr); return None

def get_slugs(token):
    r = urllib.request.Request(f'https://codeload.github.com/{REPO}/tar.gz/refs/heads/{BRANCH}',
                               headers={'Authorization': f'Bearer {token}', 'User-Agent': 'conveyor-helper'})
    data = urllib.request.urlopen(r, timeout=300).read()
    slugs = set()
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        for m in t.getmembers():
            if m.isfile() and ('/articles/blog/' in m.name or '/articles/pain/' in m.name) and m.name.endswith('.json'):
                slugs.add(m.name.split('/')[-1][:-5])
    return slugs

def make_og(og_title, og_cat, footer_l, footer_r):
    from PIL import Image, ImageDraw, ImageFont
    font_path = None
    try:
        css = urllib.request.urlopen(urllib.request.Request(
            'https://fonts.googleapis.com/css2?family=Manrope:wght@800&display=swap',
            headers={'User-Agent': 'Opera/9.80 (Windows NT 5.0; U; ru) Presto/2.10.289 Version/10.00'}),
            timeout=30).read().decode()
        urls = re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+\.(?:ttf|otf))\)', css)
        if urls:
            d2 = urllib.request.urlopen(urllib.request.Request(urls[0], headers={'User-Agent': 'Opera/9.80'}), timeout=30).read()
            open('/tmp/manrope.ttf', 'wb').write(d2); font_path = '/tmp/manrope.ttf'
    except Exception:
        pass
    if not font_path:
        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    W, H = 1200, 630
    img = Image.new('RGB', (W, H), (14, 16, 19))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 16, H], fill=(255, 196, 0))
    f_cat, f_title, f_foot = ImageFont.truetype(font_path, 30), ImageFont.truetype(font_path, 56), ImageFont.truetype(font_path, 26)
    d.text((64, 104), og_cat, font=f_cat, fill=(255, 196, 0))
    def wrap(t, maxw):
        lines, cur = [], ''
        for w_ in t.split():
            test = (cur + ' ' + w_).strip()
            if d.textlength(test, font=f_title) <= maxw: cur = test
            else:
                if cur: lines.append(cur)
                cur = w_
        if cur: lines.append(cur)
        return lines
    y = 186
    for ln in wrap(og_title, W - 64 - 70):
        d.text((64, y), ln, font=f_title, fill=(245, 247, 250)); y += 72
    d.line([(64, H - 118), (W - 64, H - 118)], fill=(52, 58, 66), width=2)
    d.text((64, H - 90), footer_l, font=f_foot, fill=(140, 148, 158))
    dw = d.textlength(footer_r, font=f_foot)
    d.text((W - 64 - dw, H - 90), footer_r, font=f_foot, fill=(140, 148, 158))
    buf = io.BytesIO(); img.save(buf, 'PNG')
    return buf.getvalue()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', required=True)
    ap.add_argument('--og-title')
    ap.add_argument('--og-cat', default='Зарядка')
    ap.add_argument('--og-footer-l', default='ЗАПАС ХОДА · ПРАКТИКА EV В РОССИИ')
    ap.add_argument('--og-footer-r', default='zapashoda-ev.ru')
    ap.add_argument('--check-only', action='store_true')
    a = ap.parse_args()
    token = None
    for k in ('GIT_TOKEN', 'GITHUB_TOKEN', 'TURBO_GITHUB_TOKEN'):
        if os_env(k): token = os_env(k); break
    if not token:
        print('ERROR: set GIT_TOKEN env', file=sys.stderr); sys.exit(2)
    art = json.load(open(a.json, encoding='utf-8'))
    slug = art['slug']
    # --- validations ---
    slugs = get_slugs(token)
    if slug in slugs:
        print(f'FAIL SLUG_TAKEN: {slug}'); sys.exit(1)
    body = art['body_html']
    assert body.startswith('<div class="art-body">') and body.rstrip().endswith('</div>'), 'body wrapper'
    inner = sorted(set(re.findall(r'href="(/[^"]+)"', body)))
    if len(inner) < 8: print(f'FAIL LINKS <8: {len(inner)}'); sys.exit(1)
    whitelist = {'/catalog/', '/models/', '/b2b/'}
    missing = [s for s in inner if s not in whitelist and s.strip('/').split('/')[-1] not in slugs]
    if missing: print(f'FAIL BROKEN_LINKS: {missing}'); sys.exit(1)
    if '₽' in json.dumps(art.get('faq', []), ensure_ascii=False): print('FAIL RUBLE_IN_FAQ'); sys.exit(1)
    if re.search(r'[a-z]\.[а-яё]', body): print('FAIL LATIN_DOT_CYR'); sys.exit(1)
    words = len(re.findall(r'[а-яА-ЯёЁ]+', re.sub(r'<[^>]+>', ' ', body)))
    if not (500 <= words <= 950): print(f'FAIL WORDS {words} not in 500-950'); sys.exit(1)
    if len(art['title']) > 57: print(f"FAIL TITLE {len(art['title'])} > 57"); sys.exit(1)
    print(f'OK: slug free, {len(inner)} links, {words} words')
    if a.check_only: return
    og_title = a.og_title or art['title']
    og_bytes = make_og(og_title, a.og_cat, a.og_footer_l, a.og_footer_r)
    b1 = req(f'{API}/git/blobs', 'POST', {'content': base64.b64encode(json.dumps(art, ensure_ascii=False).encode()).decode(), 'encoding': 'base64'}, token)
    b2 = req(f'{API}/git/blobs', 'POST', {'content': base64.b64encode(og_bytes).decode(), 'encoding': 'base64'}, token)
    assert b1 and b2, 'blob fail'
    for attempt in range(3):
        head = req(f'{API}/git/ref/heads/{BRANCH}', token=token)
        bc = req(f'{API}/git/commits/{head["object"]["sha"]}', token=token)
        tree = req(f'{API}/git/trees', 'POST', {'base_tree': bc['tree']['sha'], 'tree': [
            {'path': f'site/src/data/articles/blog/{slug}.json', 'mode': '100644', 'type': 'blob', 'sha': b1['sha']},
            {'path': f'site/public/assets/og/b-{slug}.png', 'mode': '100644', 'type': 'blob', 'sha': b2['sha']}]}, token)
        c = req(f'{API}/git/commits', 'POST', {'message': f'blog: {art["title"]}', 'tree': tree['sha'], 'parents': [head['object']['sha']]}, token)
        if c:
            u = req(f'{API}/git/refs/heads/{BRANCH}', 'PATCH', {'sha': c['sha'], 'force': False}, token)
            if u: print(f'PUBLISHED commit {c["sha"]}'); return
        time.sleep(15)
    print('FAIL HEAD_MOVED after 3 attempts'); sys.exit(1)

def os_env(k):
    import os
    return os.environ.get(k)

if __name__ == '__main__':
    main()
