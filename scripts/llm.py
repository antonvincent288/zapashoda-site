#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-цепочка для статей «Запас хода»: GigaChat → Groq → GitHub Models → шаблонный пост.
Все провайдеры опциональны: отсутствие ключа просто пропускает уровень.
Строго: НЕ выдумывать цифры. Всё, чего нет в source_text, — нельзя писать.
"""
import os, json, uuid, re, html, urllib.request, urllib.error

PROMPT = """Ты — редактор Telegram-канала «Запас хода» о практическом владении электромобилем в России.
Напиши короткую статью (600–1500 знаков) по материалам ИСТОЧНИКА ниже.

Правила:
- Только факты из источника. НИКАКИХ цифр, которых нет в тексте источника. Если цифр нет — не добавляй.
- Стиль: короткие абзацы, конкретика, без слов «революция», «прорыв», «шок», «эксперты назвали».
- Структура: 3–6 абзацев, в конце один абзац «Что это значит для владельца» (1–2 предложения, практический смысл).
- Не пиши «по сообщениям СМИ» — пиши суть.

ИСТОЧНИК:
{source}

Верни строго JSON без markdown-обёртки:
{{"title": "заголовок до 70 знаков", "teaser": "анонс до 180 знаков", "body_html": "<p>абзац</p><p>…</p> — только теги <p>, <b>, <ul><li>"}}"""

def _post_json(url, headers, payload, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))

def _extract_json(text):
    m = re.search(r'\{.*\}', text, re.S)
    if not m: return None
    try:
        obj = json.loads(m.group(0))
        if obj.get('title') and obj.get('body_html'): return obj
    except Exception: pass
    return None

def _sanitize(obj):
    t = obj.get('title','').strip()[:80]
    te = obj.get('teaser','').strip()[:200]
    b = obj.get('body_html','')
    # только безопасные теги
    b = re.sub(r'(?i)</?(?!(p|b|ul|li|ol)\b)[a-z0-9/="' + "']*>", '', b)
    if not (t and len(b) > 150): return None
    return {'title': t, 'teaser': te, 'body': b}

def giga(source, key):
    if not key: return None
    try:
        import ssl
        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        tok = urllib.request.Request('https://ngw.devices.sberbank.ru:9443/api/v2/oauth',
            data=b'scope=GIGACHAT_API_PERS',
            headers={'Authorization': 'Basic ' + key, 'RqUID': str(uuid.uuid4()), 'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST')
        with urllib.request.urlopen(tok, timeout=30, context=ctx) as r:
            access = json.loads(r.read().decode())['access_token']
        resp = _post_json('https://gigachat.devices.sberbank.ru/api/v1/chat/completions',
            {'Authorization': 'Bearer ' + access, 'Content-Type': 'application/json'},
            {'model': 'GigaChat', 'messages': [{'role': 'user', 'content': PROMPT.format(source=source[:6000])}], 'temperature': 0.5})
        return _extract_json(resp['choices'][0]['message']['content'])
    except Exception as e:
        print('giga fail:', str(e)[:120]); return None

def groq(source, key):
    if not key: return None
    try:
        resp = _post_json('https://api.groq.com/openai/v1/chat/completions',
            {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
            {'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': PROMPT.format(source=source[:6000])}], 'temperature': 0.5})
        return _extract_json(resp['choices'][0]['message']['content'])
    except Exception as e:
        print('groq fail:', str(e)[:120]); return None

def gh_models(source):
    tok = os.environ.get('GITHUB_TOKEN')
    if not tok: return None
    try:
        resp = _post_json('https://models.github.ai/inference/chat/completions',
            {'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'},
            {'model': 'openai/gpt-4o-mini', 'messages': [{'role': 'user', 'content': PROMPT.format(source=source[:6000])}], 'temperature': 0.5})
        return _extract_json(resp['choices'][0]['message']['content'])
    except Exception as e:
        print('gh-models fail:', str(e)[:120]); return None

def template_article(title, src_text, url):
    """Шаблонный пост: только факты из источника, без генерации."""
    import urllib.parse
    host = urllib.parse.urlparse(url).netloc
    s = src_text[:1200]
    sentences = re.split(r'(?<=[.!?])\s+', s)
    bullets = ''.join('<li>' + html.escape(x.strip()[:200]) + '</li>' for x in sentences[:4] if len(x.strip()) > 20)
    body = ('<p>' + html.escape(title) + '. Что известно из источника:</p><ul>' + bullets + '</ul>'
     '<p>Полный текст — в источнике: <a href="' + html.escape(url) + '">' + html.escape(host) + '</a>.</p>'
     '<p><b>Что это значит для владельца:</b> следим за подробностями — разбор появится, когда будут подтверждённые детали.</p>')
    teaser = html.escape(sentences[0].strip()[:170]) if sentences else html.escape(title)
    return {'title': html.escape(title)[:80], 'teaser': teaser, 'body': body}

def write_article(title, src_text, url):
    art = None
    art = giga(src_text, os.environ.get('GIGA_AUTH_KEY')) or groq(src_text, os.environ.get('GROQ_API_KEY')) or gh_models(src_text)
    if art:
        art = _sanitize(art)
        if art:
            art['provider'] = 'llm'
            return art
    print('LLM недоступна — шаблонный пост')
    art = template_article(title, src_text, url)
    art['provider'] = 'template'
    return art
