# Conveyor helpers

Набор скриптов-помощников для конвейера контента zapashoda-ev.ru (уровень 1, без ключей владельца).

## make_article.py — валидация + публикация статьи одним прогоном
Вход: article.json (slug, title, desc, category, read_min, date, og, body_html, faq).
Валидация перед пушем: свободный слаг (по tarball), >=8 внутренних ссылок, 500–950 слов,
никаких ₽ в FAQ, нет латинской точки перед кириллицей, все внутренние ссылки резолвятся.
OG-картинка 1200x630 (PIL, Manrope с UA-хаком, fallback DejaVu).
Пуш: blobs -> tree -> commit -> ref с retry при HEAD_MOVED.

```bash
export GIT_TOKEN=github_pat_...
python tools/conveyor/make_article.py --json article.json --og-title "Заголовок OG" --og-cat "Зарядка"
python tools/conveyor/make_article.py --json article.json --check-only   # только валидация
```

## verify_prod.py — прод-верификация с retry против CDN-кэша
Проверяет 200 + FAQPage + плашку "Актуально: DD.MM.YYYY" + probe-фразы + OG 200.

```bash
python tools/conveyor/verify_prod.py --slug my-slug --badge 11.11.2026 \
  --probe "WattSaving" --probe "56 кВт·ч" --max-tries 10 --sleep 95
```

## bridge_push.py — append отчёта в bridge/alisa_to_architect.json (main)
```bash
export GIT_TOKEN=... && python tools/conveyor/bridge_push.py --id Z-20261110XX --topic "..." --body-file report.txt
```

## Правила конвейера (кратко, для агентов)
1. Токен — только через env (GIT_TOKEN), никогда не хардкодить.
2. Цены ₽ — только в body_html; FAQ — словами.
3. Внутренние ссылки сверять по слагам tarball ДО пуша (blog И pain; whitelist: /catalog/, /models/, /b2b/).
4. Никакой literal-конкатенации слагов внутри многострочных строк — вставлять явно.
5. Публикация -> verify_prod -> bridge_push (в этом порядке, в одном прогоне).
