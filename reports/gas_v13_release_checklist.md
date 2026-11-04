# RELEASE-чек-лист: дельты GAS v13 (R-05, R-09)

**Статус: дельты подготовлены, на прод GAS НЕ вставлены (право вставки — владельца).**
Тесты GAS из Actions недоступны — сначала dry_run, потом живой запуск.

## 1. Вставка
1. Открыть GAS-проект контура (Extensions → Apps Script).
2. Новый файл `bonus_auction.gs` → вставить `gas_v13_bonus_auction_delta.gs`.
3. Новый файл `webhook_refund.gs` → вставить `gas_v13_webhook_refund_delta.gs`.
4. Оба флага вверху: `BONUS_DRY_RUN = true`, `REFUND_DRY_RUN = true` — НЕ переключать до тестов.

## 2. Тест (dry_run)
1. В редакторе: `computeBonus('adapter-premium', 40000)` → ожидается `{status:'dry_run', details:{cls:'fast', final:2000}}`.
2. `computeBonus('bundle-set', 100000)` → `{cls:'notliquid', final:13000}` (13% маржи, потолок 15000).
3. `validateVIN('WAUZZZ8V9KA123456')` — замени на реальный VIN своей машины; неверный VIN (17 знаков с ошибкой чексуммы) → false.
4. `handleRefund({token:'TEST', vin:'<реальный VIN>', reason:'test'})` → `{status:'ok', details:[...dry_run...]}`.

## 3. Включение
1. Если dry_run зелёный — `BONUS_DRY_RUN=false`, `REFUND_DRY_RUN=false`, Deploy → New version.
2. Триггер: `updateBonusRates()` — time-driven, ежедневно 06:00 MSK.
3. Живой тест возврата: вернуть один реальный заказ через банк → проверить revoke и холд.

## 4. Ограничения (честно)
- «Отрицательный холд −200 000» — из ТЗ; в дельте реализован как константа hold; если смысл иной (штраф партнёру), подтверди значение перед включением.
- Job Bonus-Security-Test в turbo.yml требует доступа Actions к GAS — это отдельная настройка (deployment key / clasp). Пока только ручной selfTest в редакторе GAS.
