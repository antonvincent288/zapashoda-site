# Бэклог улучшений zapashoda-ev.ru — по итогам GitHub-разведки и GEO-аудита (06.11.2026)

Источники: GitHub Search API (astrowind-экосистема, astro seo/perf/a11y/ecommerce), README ключевых репо,
реальный GEO-аудит прода (geo-optimizer-skill). Владелец поручил: «иди обходи GitHub и ищи все решения
для улучшения сайта — дизайн, вёрстка, SEO и т.д.».

## Замер до правок (прод, 06.11)
GEO-SCORE: **72/100 GOOD** (bands: 68–85). Диагностика: RAG chunk readiness 53/100, Trust stack D (10/25),
Content decay risk HIGH (temporal-упоминания «до конца 2026»), Perplexity 40/100, Google AI 66/100, ChatGPT 73/100.
Полный отчёт: geoready.dev/report/audit?url=https://zapashoda-ev.ru (регенерировать после волн).

## P0 — сделано сразу (AEO-волна, коммит ниже)
1. WebSite JSON-LD на главной + sameAs (Telegram) в Organization — [astro-seo, jdevalk/seo-graph паттерны].
2. Article schema: author (Organization) + dateModified — закрывает G-BYLINE и G-DATES частично [GEO audit п.1-2].
3. Статические AI-эндпоинты: /.well-known/ai.txt, /ai/summary.json, /ai/faq.json, /ai/service.json
   [geo-optimizer-skill 1287★, aeo.js 146★ — уже сгенерированы].
Осталось из списка аудита (исполняется следующими заходами):
4. RSS/Atom feed + <link rel=alternate> в head (нужен билд-шаг или статика с регенерацией).
5. SearchAction — ТОЛЬКО после реальной страницы поиска (не делать фейковый target).
6. Формы: 3 из 12 без labels/aria-label — пройтись по OrderForm/lead-виджету.
7. Alt-тексты изображений (аудит: 1/1 img без alt — найти конкретный img).
8. Разбить контент на RAG-чанки 100–150 слов с заголовками-вопросами (chunk readiness 53→80+).
9. dateModified-мета на видимых датах статей («Обновлено: …» уже есть — сделать машиночитаемым).

## P1 — шаблон и типографика
- tailwindcss-typography (6485★): сверить наш .article с prose-конвенциями (h2/h3 spacing, ul/li, blockquote, code,
  ссылки) — перенять межабзацные интервалы и max-width чтения; без установки плагина, сравнением правил.
- accessible-astro-starter (1191★) / astro-paper (5183★): skip-link «К содержанию», :focus-visible стили,
  landmarks (main/nav/footer aria) — прогон по ZhLayout.
- astro-font (202★): preload основного начертания Inter (woff2), font-display:swap, subset cyrillic.
- withastro/storefront (833★) / astro-ecommerce (500★): паттерны карточек товара — sticky buy-bar на товарных
  страницах (pz-buy из старого CSS), сравнение в 1 клик.

## P2 — экосистема AstroWind
- Дифф с апстримом astrowind (6124★) раз в месяц: что нового в компонентах/фиксах — наша миграция на ветке
  astrowind-migration, уместно подтягивать полезное.
- alextim/astro-lib (134★): robots.txt+sitemap+manifest — у нас всё есть; идея — валидатор на CI.
- jdevalk/specification.website (922★): agent-readiness (HTML-спека, машинная читаемость) — совпадает с треком AEO.

## Текущие долги сайта (переносится из рубрики)
- Тела forum/credits — старые классы без стилей.
- Золото инлайн в телах статей (grep data/*.json — не пройден).
- Перепаковка заголовков pain-статей в SEO-крючки (нужен факт-чек каждой).
- B2B-блоки в blog-статьях.
- E-E-A-T: страница методологии/источников, авторство.

## Правило
Каждый пункт = измеримый результат (счёт аудита, Lighthouse, чек-лист рубрики). После каждой волны — повторный
GEO-аудит и прогон geometry-правила #15 по всем контейнерам.

## Вторая разведка GitHub (26 запросов, 51 репо) — дополнения 06.11
- RelayStack/astro-seo-toolkit (zero-dep: llms.txt/JSON-LD/IndexNow/sitemap) — паттерн для CI-валидации SEO-артефактов.
- casoon/astro-sitemap — sitemap с hreflang + RSS на этапе сборки; наш RSS сделан руками (endpoint rss.xml.js) — регенерируется при каждом деплое.
- RafidMuhymin/astro-imagetools (432★) — оптимизация изображений; применять при появлении фото-контента.
- starwind-ui (760★) — доступные Tailwind-компоненты для Astro; референс для чек-листа a11y.
- StJudeWasHere/seonaut (860★) — краулер-аудит SEO (битые ссылки, меты) — кандидат на периодический прогон по 400+ URL.
- martrapp/astro-vtbot (365★) — View Transitions для плавной навигации между статьями — P2.
- ReunMedia/astro-og-images — генерация уникальных OG-картинок на билде — P2 для CTR в соцсетях.
- ihuzaifashoukat/llmoptimizer — регенерация llms.txt (у нас статичный — сверять с изменениями каталога).
