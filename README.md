# Запас хода — сайт (zapashoda-site)

SEO-сайт «Запас хода»: 137 страниц моделей, 12 руководств, каталог новостей со своей страницей у каждой статьи, VIN-справочник, карта зарядных станций (OSM), llms.txt, OG-карточки, RSS.

Всё бесплатно: GitHub Pages (хостинг) + GitHub Actions (сбор новостей и деплой). Домен: **zapashoda-ev.ru** (reg.ru), хостинг не нужен.

## Запуск локально / в Actions

```bash
python3 -m pip install pillow
python3 build.py _site   # сборка в папку _site
```

В Actions это делает workflow `.github/workflows/site.yml`:
каждые 3 часа — сбор новостей (collector), генерация статей через LLM-цепочку, коммит в репо, пересборка сайта, деплой на ветку `gh-pages`.

## Первый деплой (5 шагов)

1. Создайте **публичный** репозиторий `zapashoda-site` на GitHub.
2. Загрузите все файлы из этого архива в корень репо (веб-интерфейс: «uploading an existing file» → перетащить содержимое архива).
3. Дождитесь первого прогона Actions (или нажмите «Run workflow»). Ветка `gh-pages` создастся автоматически.
4. Settings → Pages → Source: **Deploy from a branch** → ветка `gh-pages`, папка `/ (root)`. Save.
5. Добавьте DNS у регистратора домена:
   - A-записи: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - CNAME для `www` → `antonvincent288.github.io`
   - HTTPS включится автоматически после привязки домена в Settings → Pages → Custom domain.

## Секреты (Settings → Secrets and variables → Actions)

| Секрет | Обязателен? | Зачем |
|---|---|---|
| `GIGA_AUTH_KEY` | нет (рекомендуется) | Ключ GigaChat (developers.sber.ru → Studio → Настройки API → Получить ключ). Основной писатель статей. |
| `GROQ_API_KEY` | нет | Фолбэк №1 (free, без карты, Groq Console). |
| `GITHUB_TOKEN` | автоматом | Фолбэк №2 (GitHub Models) — выдаётся сам, ничего не делаем. |

Без ключей статьи будут шаблонными (заголовок + тезисы + ссылка на источник) — сайт всё равно собирается и деплоится.

## Смена домена

Домен уже вшит: дефолт `https://zapashoda-ev.ru` в `build.py` и `cname: zapashoda-ev.ru` в workflow.
Если поменяете домен: поменяйте дефолт в `build.py` (или задайте переменную репо `SITE_DOMAIN` в Settings → Secrets and variables → Actions → Variables) и в `cname:` в workflow. Перезапустите workflow.

## Структура репо

```
build.py                 — генератор сайта (данные моделей зашиты внутрь)
data/news/*.json         — статьи (9 стартовых + добавленные collector'ом)
data/news_map.json       — map slug → message_id поста в TG (заполняет GAS v3.5)
data/seen.json           — дедуп collector'а
scripts/collector.py     — сборщик новостей (Bing RSS + дедуп + скоринг)
scripts/llm.py           — LLM-цепочка: GigaChat → Groq → GitHub Models → шаблон
static/leaflet/*         — файлы Leaflet для карты ЗУ
assets/fonts/*           — шрифты для OG-карточек
_site/                   — готовая сборка (можно деплоить прямо с первого пуша)
.github/workflows/site.yml — автопайплайн
```

## Как работают комментарии под новостями

Под каждой статьёй — кнопка «Обсудить в Telegram»: ведёт в тред обсуждения тизер-поста
в канале (нужна группа обсуждения, привязанная к каналу). Пока `data/news_map.json` пуст —
кнопка ведёт на канал целиком. Когда GAS v3.5 сохранит message_id поста (slug → message_id),
при следующей сборке ссылка станет точной: `t.me/zapashoda_ev/<message_id>`.

## Данные и лицензии

- Карта: © участники OpenStreetMap (ODbL), запросы через Overpass API — указание источника обязательно (в футере есть).
- Модели/боли: собственная база проекта.
