# GAS v12 — РЕЛИЗ (03.11.2026, приказ владельца)

## Состав
- `gas_v12_shop_products_audit.js` — дельта к v11 (вставлять В КОНЕЦ кода v11 в Apps Script).

## Боевые решения владельца
1. Цена КАЖДОГО гайда — **990 ₽** (М-4, М-11, М-12, ЖК-паркинг) — `SHOP_PRODUCTS`, все `amount: 99000` копеек.
2. B2B-бонус менеджеру — **2 000 ₽** (`B2B_BONUS_RUB`).
3. Двухэтапный холд бонуса: заявка → `pending` → вебхук paid → `hold` → сверка факта оплаты + валидный VIN → `paid` / иначе `rejected`. VIN по ISO 3779: 17 символов, I/O/Q запрещены; чек-сумма — предупреждение (не отказ).
4. Мульти-продуктовый Init (`_shopInitProducts`) — сумма берётся из Script Properties (`shop_products`), смена цены — `shopSetProductPrice(slug, руб)` без правки кода.

## Установка (5 минут)
1. Открыть Apps Script проекта, вставить содержимое `gas_v12_shop_products_audit.js` **в конец** существующего кода v11.
2. В функции `_odDoPost` рядом с другими ветками добавить:
   - `if (p.t === 'shop_init') return _shopInitProducts(p);`  ← ЗАМЕНИТЬ старую ветку shop_init на эту (новая логика продукта).
   - `if (p.t === 'bonus_selftest') return _bonusSelftestEndpoint();`  ← монитор из Actions.
3. В обработчике вебхука Т-Кассы после подтверждения статуса PAID добавить вызов: `bonusOnWebhookPaid(orderId);`
4. В обработчике od_order (заявка) добавить: `bonusOnOrder(orderId, product, email, ref, managerTg);`
5. Разово выполнить в редакторе: `shopSetProducts()` и `bonusSelfTest()`.
6. Сохранить. Деплой не требуется (это Apps Script) — проверить кнопкой на /shop/digital/.

## Проверка после установки
- `bonusSelfTest()` в логе: строк листа «Бонусы», бонус 2 000 ₽, цепочка pending→hold→paid/rejected.
- Кнопка «Купить за 990 ₽» на /shop/digital/ → тестовая карта 4300 0000 0000 0777 (терминал DEMO 1793665379484DEMO) → письмо + success-страница + одноразовый токен.
- `AI_BRIDGE.json` tinkoff_status → `test`.

## Автоконтроль
Ежедневный cron `gas-monitor.yml` дергает `bonus_selftest` и пишет вердикт в мост
(«GAS live, продукты 4×990 ₽, бонус 2 000 ₽» — или «GAS не вставлен», если ещё нет).
