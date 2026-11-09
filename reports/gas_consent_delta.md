# ДЕЛЬТА GAS: согласие на обработку ПДн

*Для владельца: вставить в Apps Script приёмника ДО слияния ветки privacy-rollout в astrowind-migration. Без дельты уведомления о лидах сайта пропадут: сейчас их шлёт клиентский скрипт, после мержа клиентский дубль отключён (токен бота убран из HTML).*

1. Таблица лидов: колонки `Consent`, `ConsentTS`, `PolicyVersion`.
2. Фильтр: заявки без согласия не записываются.
3. Уведомление: лид сайта (t='lead') теперь уведомляет в Telegram через GAS.

Точные правки:

**1) Заголовки нового листа** — строку appendRow заголовков заменить на:
```js
sh.appendRow(['Дата','Тип','Модель','Город','Имя','Телефон','Позиций','Сумма ₽','Комментарий','Состав','Consent','ConsentTS','PolicyVersion']);
```
**2) Фильтр согласия** — после строки `if (String(d.t || '') === 'od_order') return _odDoOrder(d);`:
```js
if (String(d.consent || '') !== 'yes') { return out({ ok: false, error: 'consent required' }); }
```
**3) Ветка t='lead'** — заменить appendRow на (добавить 3 последних значения):
```js
        d.consent || '',
        d.consent_ts || '',
        d.policy_version || ''
```
и после него:
```js
try { tgSend('🆕 Лид сайта\n👤 ' + (d.name || '—') + '\n📞 ' + (d.contact || '—') + '\n📍 ' + (d.city || '—') + '\n🚗 ' + (d.carModel || '—') + (d.product ? ('\n📦 ' + d.product) : '') + (d.comment ? ('\n💬 ' + d.comment) : '')); } catch (eNotify) {}
```
**4) Общий appendRow (миниапп/корзина)** — дополнить в конце: `itemsText, d.consent || '', d.consent_ts || '', d.policy_version || ''`.

Проверка: тест-заявка с галочкой → строка с Consent=yes + уведомление; POST без consent → ok:false.
