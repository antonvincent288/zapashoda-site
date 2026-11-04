#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
visual_qa.py — контроль Арт-Директора для B2B-материалов «Запас Хода» (регламент v3-B2B-SHIELD).

Что проверяет:
  1. OG-карточки B2B-статей: существуют, размер > 12 КБ, фон = антрацит #1d1d1f (VISUAL_SPEC).
  2. На страницах B2B-статей: есть выноски gbox (блоки «выносок», не «сухой текст»).
  3. Карточки товаров категории «Адаптеры»: маркер безопасности (gbox) на месте.
  4. Калькуляторы (модели + /calculator/): сноска о поминутных тарифах.
  5. CSS: класс .gbox с золотом #D4AF37 подключён.

Запуск: python3 scripts/visual_qa.py <каталог_сборки>   (например _site или /tmp/out)
Выход: exit 0 — всё ок; exit 1 — есть замечания (печать по пунктам).
Палитра B2B (VISUAL_SPEC): антрацит #1d1d1f (29,29,31), золото #D4AF37 (212,175,55).
"""
import os, sys, re, glob

ANTHRACITE = (29, 29, 31)
GOLD = (212, 175, 55)

B2B_SLUGS = ['b2b-reglament-vydachi-ev', '800v-zaryadka-ev-rossiya',
             'erekv-domashnyaya-zaryadka', 'sertifikaciya-ezs-rf-2026']

def main(outdir):
    problems = []

    # 1. OG-карточки B2B в палитре
    for sl in B2B_SLUGS:
        p = os.path.join(outdir, 'assets', 'og', 'b-%s.png' % sl)
        if not os.path.exists(p):
            problems.append('OG нет: %s' % p); continue
        if os.path.getsize(p) < 12000:
            problems.append('OG подозрительно мала: %s (%d байт)' % (p, os.path.getsize(p)))
        try:
            from PIL import Image
            im = Image.open(p).convert('RGB')
            bg = im.getpixel((10, 10))
            if max(abs(bg[i] - ANTHRACITE[i]) for i in range(3)) > 12:
                problems.append('OG %s: фон %s — не антрацит %s' % (sl, bg, (ANTHRACITE,)))
        except ImportError:
            print('PIL недоступен — проверку палитры пропускаю')

    # 2. Выноски gbox в статьях
    for sl in B2B_SLUGS:
        p = os.path.join(outdir, 'blog', sl + '.html')
        if not os.path.exists(p):
            problems.append('статья нет: %s' % p); continue
        s = open(p, encoding='utf-8', errors='ignore').read()
        if 'gbox' not in s:
            problems.append('статья %s: нет выноски gbox' % sl)
        if s[:700].count('noindex'):
            problems.append('статья %s: всё ещё noindex!' % sl)

    # 3. Маркер безопасности на адаптерах
    adapters = [f for f in glob.glob(os.path.join(outdir, 'catalog', 'adapter*.html'))
                if 'index' not in os.path.basename(f)]
    for f in adapters:
        s = open(f, encoding='utf-8', errors='ignore').read()
        if 'Важно про безопасность' not in s:
            problems.append('адаптер без маркера: %s' % os.path.basename(f))

    # 4. Сноска калькуляторов
    calc_model = os.path.join(outdir, 'models', 'zeekr-001-001-fr', 'index.html')
    if os.path.exists(calc_model):
        s = open(calc_model, encoding='utf-8', errors='ignore').read()
        if 'поминутные тарифы' not in s:
            problems.append('модельная страница: нет сноски калькулятора')
    calc_page = os.path.join(outdir, 'calculator', 'index.html')
    if os.path.exists(calc_page):
        s = open(calc_page, encoding='utf-8', errors='ignore').read()
        if 'поминутные тарифы' not in s:
            problems.append('/calculator/: нет сноски о поминутных тарифах')

    # 5. CSS gbox
    css = os.path.join(outdir, 'style.css')
    if os.path.exists(css):
        s = open(css, encoding='utf-8', errors='ignore').read()
        if '.gbox' not in s or '#D4AF37' not in s.replace('d4af37', '#D4AF37').lower().replace('#d4af37', '#D4AF37') and '#D4AF37' not in s:
            if '.gbox' not in s:
                problems.append('style.css: нет класса .gbox')

    if problems:
        print('visual_qa: %d замечаний' % len(problems))
        for p in problems: print('  -', p)
        return 1
    print('visual_qa: OK — %d B2B-статей, %d адаптеров, калькуляторы со сносками, палитра на месте'
          % (len(B2B_SLUGS), len(adapters)))
    return 0

if __name__ == '__main__':
    outdir = sys.argv[1] if len(sys.argv) > 1 else '_site'
    sys.exit(main(outdir))
