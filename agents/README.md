# Агенты-помощники zapashoda-site (турбо-конвейер)

Набор автономных помощников уровня 1: работают без LLM-ключей, на чистом Python (stdlib),
запускаются любым агентом в любом контейнере. Протокол команды — `bridge/README.md`.

## Карта команды

| Агент | Скрипт | Что делает | Выход |
|---|---|---|---|
| **Редактор-линтер** | `scripts/content_linter.py` | Типографика-гигиена, ДИРЕКТИВА ЦЕН (цены только в каталоге), дубли slug, гейт гайдов (главы/слова/FAQ) | JSON-отчёт в stdout, exit 0/1 |
| **Смок-прод** | `scripts/smoke_prod.py` | HTTP-аудит прод-страниц (200, title, canonical, og, h1), сверка sitemap | JSON-отчёт в stdout |
| **Публикатор** | `scripts/gh_put_file.py` | Заливка файла в репо с SHA-защитой (HEAD_MOVED — отказ) | коммит-sha или ошибка |
| **Каркасист** | `scripts/article_scaffolder.py` | Болванка статьи/гайда в формате `data/articles/**` | файл JSON рядом |

## Правила команды (обязательны)
1. **Прод-правка только через `gh_put_file.py`** — он сверяет SHA ветки и отказывает при `HEAD_MOVED`
   (сосед пушит активно, затирание недопустимо).
2. **Цены — только в каталоге.** Цена (`N ₽`, `от N ₽`) в `body_html` статей — ошибка (поймает линтер).
3. **Секреты не в репо, не в мост.** Токен — только через env (`GITHUB_TOKEN`).
4. **Не публиковать гайды без подтверждения владельца.** Линтер помечает гайды, но финальное «публиковать» — за человеком.
5. Статус и отчёты — в `bridge/alisa_to_architect.json` (формат в `bridge/README.md`).

## Примеры

```bash
# линтер по всем статьям (blog+pain+safety)
python3 agents/scripts/content_linter.py --root site/src/data/articles

# смок прод по списку из файла (по одному URL в строке)
python3 agents/scripts/smoke_prod.py --urls agents/urls_core.txt --base https://zapashoda-ev.ru/

# залить правленный файл
GITHUB_TOKEN=... python3 agents/scripts/gh_put_file.py --file site/src/pages/blog/x.astro --repo antonvincent288/zapashoda-site --branch astrowind-migration --message "fix: ..."

# каркас новой статьи
python3 agents/scripts/article_scaffolder.py --slug moy-novy-gaid --title "Заголовок" --section blog
```

## Уровни турбо-машины
- **Уровень 1 (сейчас):** эти помощники + `scripts/hourly_watch.py` (крон в Actions) + скилл `zapashoda-turbo-publish`.
- **Уровень 2 (ключи владельца):** CrewAI-конвейер Researcher→Writer→Editor→Publisher; Telegram-ассистент.
- **Уровень 3 (сервер):** LangGraph-оркестратор, очереди, экономический трекер к цели 5 млн ₽/мес.
