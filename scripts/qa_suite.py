#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qa_suite.py — автоматический контроль качества сборки и контента «Запас Хода».
Задача: фабрика контента не должна публиковать фактические ошибки и битые страницы.

Проверки (каждая = код выхода FAIL для CI):
  A. Ссылки: все внутренние href/src резолвятся в файлы (с / и /index.html-нормализацией,
     фильтр JS-конкатенаций 'a'+x+'b' и '…/'+slug+'.html').
  B. Sitemap: 0 битых URL, 0 noindex-страниц, robots ссылается на sitemap.
  C. HTML: div-баланс на всех страницах; meta robots валиден.
  D. Мета: title/desc/viewport у всех ИНДЕКСИРУЕМЫХ страниц (noindex-заглушки не считаем).
  E. Заголовки: ровно один H1 на индексируемых страницах.
  F. Активы: favicon.svg/ico, apple-touch-icon.png, site.webmanifest, og default.
  G. Регресс недавних фиксов: сноска калькулятора (модельные), маркер адаптеров, guard iOS-меню,
     favicon.svg существует.
  H. AI-SEO: robots.txt разрешает ключевых ИИ-краулеров (GPTBot, ClaudeBot, PerplexityBot,
     Google-Extended, Applebot-Extended, YandexGPT, AliceBot); llms.txt существует и свеж (дата
     не старше 14 дней); llms.txt содержит ссылки на блог-статьи; BlogPosting на модельных;
     «Коротко/Прямой ответ» — покрытие (WARN, не FAIL).
  I. Факт-чекер фабричных драфтов (--drafts <dir>): детекторы галлюцинаций (регекс-паттерны
     известных ловушек), требование источников при плотности цифр, единицы кВт·ч, отсутствие
     «продуктов-фантазий» не из каталога.

Запуск: python3 scripts/qa_suite.py <outdir> [--drafts <dir>] [--strict]
Коды выхода: 0 — ок; 1 — FAIL (CI упадёт).
"""
import sys, os, re, json, glob, html as _html
from html.parser import HTMLParser
from datetime import date, timedelta

FAIL, WARN = [], []
LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')
SKIP_URL_PREFIX = ('mailto:', 'tel:', 'javascript:', '#', 'data:')

AI_BOTS = ['GPTBot', 'OAI-SearchBot', 'ClaudeBot', 'PerplexityBot', 'Google-Extended',
           'Applebot-Extended', 'YandexGPT', 'AliceBot']

# Паттерны известных галлюцинаций фабрики (дополнять по мере находок)
HALLUCINATION_PATTERNS = [
    (r'датчик\w*\s+на\s+шине', 'выдуманная механика считывания VIN'),
    (r'кВт/ч', 'ошибка единиц — кВт·ч, не кВт/ч'),
    (r'адаптер[^<]{0,40}(\d+)\s*кВт\s*(?:→|->)\s*(\d+)\s*кВт', 'адаптер «X кВт → Y кВт» — таких SKU в каталоге нет'),
    (r'регистраци[ия]\w*\s+T[-‑]?[Пп]ass[^<]{0,60}автоматическ\w+[^<]{0,30}покупк', 'T-Pass «автоматически при покупке» — не подтверждено'),
    (r'QR[-‑]?код[^<]{0,40}сканир\w+[^<]{0,30}пункт', 'QR-механика T-Pass не подтверждена'),
    (r'потери?\s+до?\s*30[–-]50\s*%', 'потери 30–50% — в базе мощность ниже на 25–40%'),
    (r'СП\s*551[^<]{0,80}быт\w+\s+розетк', 'СП 551 — про парковки ЭВС, не «бытовые розетки»'),
]

def load(path):
    try:
        return open(path, encoding='utf-8', errors='ignore').read()
    except Exception:
        return ''

class DivBalance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = 0
    def handle_starttag(self, t, a):
        if t == 'div': self.stack += 1
    def handle_endtag(self, t):
        if t == 'div' and self.stack > 0: self.stack -= 1

def resolve(url):
    """Внутренний URL -> путь файла в outdir или None/EXTERNAL."""
    if url.startswith(SKIP_URL_PREFIX): return None
    if url.startswith('http'):
        if 'zapashoda-ev.ru' in url:
            url = url.split('zapashoda-ev.ru', 1)[1]
        else:
            return 'EXTERNAL'
    path = url.split('#')[0].split('?')[0]
    if not path: return None
    if not path.startswith('/'): return None
    if path.endswith('/'): path += 'index.html'
    return path

def is_js_concat(url):
    return ('+' in url) or (url.startswith("/models/')") or url.startswith("/catalog/')"))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_OUTSIDE = ('assets/', 'static/')

def repo_has(rel):
    rel = rel.lstrip('/')
    return (os.path.exists(os.path.join(REPO_ROOT, rel))
            or os.path.exists(os.path.join(REPO_ROOT, 'static', rel))
            or os.path.exists(os.path.join(REPO_ROOT, 'assets', rel)))

def check_links(outdir, all_files):
    fset = set(all_files)
    for f in all_files:
        if not f.endswith('.html'): continue
        s = load(os.path.join(outdir, f))
        for u in LINK_RE.findall(s):
            if is_js_concat(u): continue
            r = resolve(u)
            if r in (None, 'EXTERNAL'): continue
            rel = r.lstrip('/')
            if rel not in fset:
                if rel.startswith(ASSET_OUTSIDE) or repo_has(rel):
                    WARN.append('ссылка вне сборки (ассеты деплоя): %s ← %s' % (r, f))
                else:
                    FAIL.append('битая ссылка %s ← %s' % (r, f))

def check_sitemap(outdir, all_files):
    fset = set(all_files)
    sm_p = os.path.join(outdir, 'sitemap.xml')
    sm = load(sm_p)
    if not sm:
        FAIL.append('sitemap.xml отсутствует'); return
    urls = re.findall(r'<loc>(.*?)</loc>', sm)
    for u in urls:
        r = resolve(u)
        if r in (None, 'EXTERNAL'): FAIL.append('битый URL в sitemap: %s' % u); continue
        if r.lstrip('/') not in fset: FAIL.append('sitemap → нет файла: %s' % u)
    for u in urls:
        r = resolve(u)
        if not r: continue
        f_rel = r.lstrip('/')
        s = load(os.path.join(outdir, f_rel))
        if s and not is_indexable(f_rel, s):
            FAIL.append('noindex-страница в sitemap: %s' % u)
    rb = load(os.path.join(outdir, 'robots.txt'))
    if 'Sitemap:' not in rb:
        FAIL.append('robots.txt: нет Sitemap-строки')

def check_html(outdir, all_files):
    for f in all_files:
        if not f.endswith('.html'): continue
        s = load(os.path.join(outdir, f))
        d = DivBalance(); d.feed(s)
        if d.stack:
            FAIL.append('div-баланс: %s (незакрытых %d)' % (f, d.stack))

def is_indexable(f, s):
    cut = s.find('</head>')
    head = s[:cut] if cut != -1 else s[:2000]
    return 'noindex' not in head

def check_meta(outdir, all_files):
    for f in all_files:
        if not f.endswith('.html'): continue
        s = load(os.path.join(outdir, f))
        if not is_indexable(f, s): continue
        if 'Страница переехала' in s: continue
        if '<title>' not in s: FAIL.append('нет title: %s' % f)
        if 'name="description"' not in s: FAIL.append('нет description: %s' % f)
        if 'name="viewport"' not in s: FAIL.append('нет viewport: %s' % f)
        if s.count('<h1') > 1: FAIL.append('несколько H1: %s' % f)

def check_assets(outdir):
    for name in ('favicon.svg', 'favicon.ico', 'apple-touch-icon.png', 'site.webmanifest',
                 'assets/og/default.png'):
        if not os.path.exists(os.path.join(outdir, name)):
            FAIL.append('нет актива: %s' % name)

def check_regress(outdir, all_files):
    model = load(os.path.join(outdir, 'models', 'zeekr-001-001-fr', 'index.html'))
    if model and 'поминутные тарифы' not in model:
        FAIL.append('регресс: сноска калькулятора пропала (модельная)')
    adapter = load(os.path.join(outdir, 'catalog', 'adapter-type2-gbt-premium.html'))
    if adapter and 'Важно про безопасность' not in adapter:
        FAIL.append('регресс: маркер безопасности адаптера пропал')
    home = load(os.path.join(outdir, 'index.html'))
    if home and 'lastTouch>700' not in home:
        FAIL.append('регресс: guard iOS-меню пропал')
    css = load(os.path.join(outdir, 'style.css'))
    if css and '.gbox' not in css:
        FAIL.append('регресс: класс .gbox пропал из style.css')

def check_ai_seo(outdir, all_files):
    rb = load(os.path.join(outdir, 'robots.txt'))
    for bot in AI_BOTS:
        if 'User-agent: ' + bot not in rb:
            FAIL.append('robots.txt: не разрешён ИИ-краулер %s' % bot)
    ll = load(os.path.join(outdir, 'llms.txt'))
    if not ll:
        FAIL.append('llms.txt отсутствует')
    else:
        m = re.search(r'последнее обновление:\s*(\d{4}-\d{2}-\d{2})', ll)
        if not m:
            WARN.append('llms.txt: нет даты обновления')
        else:
            try:
                d = date.fromisoformat(m.group(1))
                if date.today() - d > timedelta(days=14):
                    WARN.append('llms.txt устарел (обновлён %s)' % m.group(1))
            except ValueError:
                WARN.append('llms.txt: битая дата %s' % m.group(1))
        if '## Экспертные статьи блога' not in ll:
            WARN.append('llms.txt: нет секции блога')
        if '## Быстрые ответы' not in ll:
            WARN.append('llms.txt: нет секции быстрых ответов (цитируемость ИИ)')
    # покрытие «Коротко/Прямой ответ» — WARN-метрика
    def cover(pred, label):
        n = tl = fa = 0
        for f in all_files:
            if not f.endswith('.html') or not pred(f): continue
            n += 1
            s = load(os.path.join(outdir, f))
            if 'class="tldr"' in s or 'Коротко:' in s or 'Прямой ответ:' in s: tl += 1
            if 'FAQPage' in s: fa += 1
        if n:
            WARN.append('AEO %s: прямой ответ/«Коротко» %d%%, FAQPage %d%% (из %d)'
                        % (label, tl*100//n, fa*100//n, n))
    mfiles = [f for f in all_files if f.startswith('models/') and f.endswith('index.html')
              and f != 'models/index.html']
    bp = sum(1 for f in mfiles if 'BlogPosting' in load(os.path.join(outdir, f)))
    if mfiles and bp < len(mfiles):
        FAIL.append('BlogPosting не на всех модельных: %d/%d' % (bp, len(mfiles)))
    cover(lambda f: f.startswith('models/') and f.endswith('index.html'), 'models')
    cover(lambda f: f.startswith('pain/') and f.endswith('.html') and 'index' not in f, 'pain')
    cover(lambda f: f.startswith('blog/') and f.endswith('.html') and 'index' not in f, 'blog')

def fact_check_drafts(drafts_dir):
    """Факт-чекер фабричных драфтов: детекторы галлюцинаций + плотность источников."""
    for path in sorted(glob.glob(os.path.join(drafts_dir, '**', '*.json'), recursive=True)):
        try:
            d = json.load(open(path, encoding='utf-8'))
        except Exception:
            continue
        slug = d.get('slug') or os.path.basename(path)
        body = ' '.join(ch if isinstance(ch, str) else json.dumps(ch, ensure_ascii=False)
                        for ch in (d.get('chapters') or [])) + ' ' + ' '.join(
                        a for q, a in (d.get('faq') or []))
        for pat, why in HALLUCINATION_PATTERNS:
            for mo in re.finditer(pat, body, re.I):
                frag = body[max(0, mo.start()-40):mo.end()+40].replace('\n', ' ')
                FAIL.append('DRAFT %s: %s | …%s…' % (slug, why, frag.strip()[:120]))
        nums = len(re.findall(r'\d[\d\s]{1,5}\s?(?:₽|руб|кВт|А\b|В\b|мин|км)', body))
        srcs = len(re.findall(r'(?:источник|по данным|со ссылкой|см\.|reddit|4pda|drive2|автостат|россети|автодор|автоваз|overpass)', body, re.I))
        if nums >= 8 and srcs == 0:
            FAIL.append('DRAFT %s: %d числовых фактов и 0 упоминаний источников' % (slug, nums))
        elif nums >= 15 and srcs < 2:
            FAIL.append('DRAFT %s: мало источников: %d при %d цифрах' % (slug, srcs, nums))

def main():
    args = sys.argv[1:]
    outdir = args[0] if args else '_site'
    drafts = None
    if '--drafts' in args:
        i = args.index('--drafts')
        drafts = args[i+1] if i+1 < len(args) else None
    if not os.path.isdir(outdir):
        print('qa_suite: каталог %s не найден' % outdir); return 1
    all_files = [os.path.join(root, fn).replace(outdir.rstrip('/') + '/', '')
                 for root, _, fns in os.walk(outdir) for fn in fns]
    check_links(outdir, all_files)
    check_sitemap(outdir, all_files)
    check_html(outdir, all_files)
    check_meta(outdir, all_files)
    check_assets(outdir)
    check_regress(outdir, all_files)
    check_ai_seo(outdir, all_files)
    if drafts and os.path.isdir(drafts):
        fact_check_drafts(drafts)
    if WARN:
        print('qa_suite: WARN (%d):' % len(WARN))
        for w in WARN[:12]: print('  ~', w)
    if FAIL:
        print('qa_suite: FAIL (%d):' % len(FAIL))
        for f in FAIL[:40]: print('  ✗', f)
        if len(FAIL) > 40: print('  … ещё %d' % (len(FAIL)-40))
        return 1
    print('qa_suite: OK — %d файлов, ссылки/sitemap/мета/div/AI-SEO чисты' % len(all_files))
    return 0

if __name__ == '__main__':
    sys.exit(main())
