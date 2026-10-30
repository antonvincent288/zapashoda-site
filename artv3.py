# -*- coding: utf-8 -*-
"""Оформление статей zapashoda-ev.ru (v3): prose-колонка, оглавление,
прогресс чтения, мета-строка, кнопки «Поделиться». Импортируется build.py и services.py."""
import re, html

_SVG = {
 'vk': 'M13.14 18.13c-6.35 0-9.97-4.35-10.12-11.6h3.18c.11 5.34 2.46 7.59 4.32 8.05V6.53h3v4.59c1.84-.2 3.77-2.29 4.42-4.59h3c-.5 2.83-2.59 4.92-4.06 5.78 1.47.69 3.86 2.5 4.76 5.79h-3.3c-.7-2.17-2.44-3.86-4.82-4.09v4.09h-.38z',
 'tg': 'M9.04 15.9l-.37 3.68c.53 0 .76-.23 1.04-.5l2.5-2.4 5.17 3.79c.95.52 1.62.25 1.87-.88l3.38-15.86c.3-1.4-.5-1.95-1.43-1.6L2.4 9.94c-1.37.53-1.35 1.3-.23 1.64l4.05 1.27 9.4-5.93c.44-.27.85-.12.52.15L9.04 15.9z',
 'wa': 'M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.17-.17.2-.35.22-.65.07-.3-.15-1.13-.42-2.15-1.33-.8-.71-1.33-1.59-1.49-1.89-.15-.3-.02-.46.13-.61.13-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.07-.15-.67-1.62-.92-2.22-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.8.37-.27.3-1.04 1.02-1.04 2.5 0 1.47 1.07 2.9 1.22 3.1.15.2 2.1 3.2 5.1 4.49.71.31 1.27.49 1.7.63.72.23 1.36.2 1.88.12.58-.09 1.76-.72 2.01-1.42.25-.7.25-1.29.17-1.42-.07-.13-.27-.2-.57-.35zM12.05 21.79h-.01a9.87 9.87 0 01-5.03-1.38l-.36-.21-3.74.98 1-3.65-.24-.37a9.86 9.86 0 01-1.51-5.26c0-5.45 4.44-9.88 9.9-9.88a9.82 9.82 0 016.99 2.9 9.83 9.83 0 012.9 7 9.9 9.9 0 01-9.9 9.89zM20.5 3.49A11.8 11.8 0 0012.05 0C5.5 0 .16 5.34.16 11.89c0 2.1.55 4.14 1.59 5.94L.06 24l6.3-1.65a11.9 11.9 0 005.68 1.45h.01c6.55 0 11.89-5.34 11.89-11.89 0-3.18-1.24-6.16-3.49-8.42z',
 'copy': 'M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V15h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z'}
_SVG['copy'] = 'M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z'
_LBL = {'vk':'ВКонтакте','tg':'Telegram','wa':'WhatsApp','copy':'Скопировать ссылку'}

def _svg(net):
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + _SVG[net] + '"/></svg>'

def _toc_html(h2s):
    items = []
    for n, (hid, txt) in enumerate(h2s, 1):
        items.append('<li><a href="#' + hid + '"><span class="toc-num">' + str(n) + '</span>' + html.escape(txt) + '</a></li>')
    return ''.join(items)

def art_enhance(body, url, title, date='', kind='Руководство'):
    plain = re.sub(r'<[^>]+>', ' ', body)
    minutes = max(1, round(len(plain.split()) / 180))
    t = re.sub(r' \| Запас хода$', '', title)
    m = re.search(r'<h2', body)
    if m and m.start() < 0.5 * len(body):
        head, rest = body[:m.start()], body[m.start():]
    else:
        head, rest = '', body
    h2s = []
    def _repl(mo):
        hid = 's%d' % (len(h2s) + 1)
        h2s.append((hid, re.sub(r'<[^>]+>', '', mo.group(1))))
        return '<h2 id="' + hid + '">' + mo.group(1) + '</h2>'
    rest = re.sub(r'<h2>(.*?)</h2>', _repl, rest)
    if len(h2s) < 2:
        h3s = []
        def _repl3(mo):
            hid = 's%d' % (len(h2s) + len(h3s) + 1)
            h3s.append((hid, re.sub(r'<[^>]+>', '', mo.group(1))))
            return '<h3 id="' + hid + '">' + mo.group(1) + '</h3>'
        rest = re.sub(r'<h3>(.*?)</h3>', _repl3, rest)
        if len(h3s) >= 3:
            h2s = h3s
    items = _toc_html(h2s) if len(h2s) >= 2 else ''
    toc_desk = ('<aside class="art-toc" aria-label="Содержание"><div class="t">Содержание</div><ol>' + items + '</ol></aside>') if items else ''
    toc_mob = ('<details class="art-tocmob"><summary>Содержание (' + str(len(h2s)) + ' разделов)</summary><ol>' + items + '</ol></details>') if items else ''
    btns = []
    for net in ['vk', 'tg', 'wa', 'copy']:
        btns.append('<a class="shbtn ' + net + '" href="#" onclick="shOpen(\'' + net + '\');return false;" title="' + _LBL[net] + '" aria-label="' + _LBL[net] + '">' + _svg(net) + '</a>')
    share = '<div class="art-share"><span class="lbl">Поделиться:</span>' + ''.join(btns) + '</div>'
    meta = ('<div class="art-meta"><span class="kind">' + html.escape(kind) + '</span><span class="dot">·</span>'
            '<span>' + str(minutes) + ' мин чтения</span><span class="dot">·</span>'
            '<span>Обновлено: ' + html.escape(date) + '</span></div>')
    return ('<div class="art"><div class="art-progress" aria-hidden="true"><i></i></div>'
            + head + meta + toc_mob
            + '<div class="art-grid">' + toc_desk + '<div class="art-body">' + rest + share + '</div></div></div>')
