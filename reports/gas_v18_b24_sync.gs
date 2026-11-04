// ==================== GAS дельта v18: Bitrix24 sync (Z-0033) ====================
// НАЗНАЧЕНИЕ: дублирует B2B-заявки (онбординг менеджеров, запрос прайса, расчёт проекта)
// и UGC-истории как лиды в Bitrix24 через входящий вебхук (crm.lead.add).
// ТРЕБОВАНИЕ: Script Property B24_WEBHOOK_URL (входящий вебхук с правом crm).
//   CRM -> Настройки -> Вебхуки -> Добавить вебхук (входящий) -> скопировать URL.
//   Script Properties -> B24_WEBHOOK_URL = <весь URL до и включая токен>.
// БЕЗ КЛЮЧА: тихий пропуск (лид в таблицу пишется как раньше, в CRM не идёт).
// ОШИБКА CRM: не ломает основную запись — всё в try/catch, статус в журнал.
// ВСТАВКА: добавить код в конец Code.gs. Тест: demoB24Sync().
// ПОДКЛЮЧЕНИЕ: в обработчиках заявок после успешной записи в лист добавить 1 строку:
//   zapB24Notify({source:'b2b_onboarding', title:'B2B: '+salon+' — '+name,
//                 comments:'QR-ID: '+(startId||'прямой')+'; Город: '+city+'; TG: @'+tg,
//                 phone:'', tg:'@'+tg});

var B24_WEBHOOK_URL = '';
(function initB24() {
  try { B24_WEBHOOK_URL = PropertiesService.getScriptProperties().getProperty('B24_WEBHOOK_URL') || ''; } catch (e) { B24_WEBHOOK_URL = ''; }
})();

function zapB24Notify(p) {
  try {
    if (!B24_WEBHOOK_URL) return { skipped: true, reason: 'no B24_WEBHOOK_URL' };
    var lead = {
      fields: {
        TITLE: (p.title || 'Заявка с сайта').substring(0, 250),
        NAME: (p.name || '').substring(0, 100),
        COMMENTS: (p.comments || '').substring(0, 4000),
        SOURCE_ID: 'WEB',
        UF_SOURCE_DESCRIPTION: (p.source || 'site') + (p.qrId ? ' (' + p.qrId + ')' : '')
      }
    };
    if (p.phone) lead.fields.PHONE = [{ VALUE: p.phone, VALUE_TYPE: 'WORK' }];
    var resp = UrlFetchApp.fetch(B24_WEBHOOK_URL + 'crm.lead.add', {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(lead),
      muteHttpExceptions: true
    });
    var code = resp.getResponseCode();
    var body = resp.getContentText();
    var ok = (code === 200) && (body.indexOf('result') !== -1);
    try { Logger.log('B24 sync: code=' + code + ' ok=' + ok + ' body=' + body.substring(0, 200)); } catch (e) {}
    return { ok: ok, code: code };
  } catch (e) {
    try { Logger.log('B24 sync error: ' + e); } catch (e2) {}
    return { ok: false, error: String(e).substring(0, 120) };
  }
}

function demoB24Sync() {
  if (!B24_WEBHOOK_URL) { Logger.log('DEMO: B24_WEBHOOK_URL не задан — добавьте Script Property и повторите.'); return; }
  var r = zapB24Notify({
    source: 'demo_test',
    qrId: 'TEST-001',
    title: 'ТЕСТ — B24-интеграция «Запас хода»',
    name: 'Алиса (тест)',
    comments: 'Тестовая запись. Источник: demoB24Sync. Если видите этот лид в CRM — интеграция работает. Удалите его.',
    phone: '+70000000000',
    tg: '@zapashoda_ev'
  });
  Logger.log('demoB24Sync result: ' + JSON.stringify(r));
  if (r.ok) Logger.log('УСПЕХ: тестовый лид создан в Bitrix24. Найдите его в CRM и удалите.');
  else Logger.log('НЕ УДАЛОСЬ: ' + JSON.stringify(r));
}
