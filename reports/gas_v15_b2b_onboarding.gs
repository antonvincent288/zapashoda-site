/**
 * ЗАПАС ХОДА — дельта v15: R-07 B2B QR-Onboarding (сбор контактов менеджеров).
 * Статус: ДЕЛЬТА ДЛЯ ВСТАВКИ ВЛАДЕЛЬЦЕМ (GAS).
 * Лист «B2B_Менеджеры»: ts, start_id, name, salon, city, telegram, status, hash_tg, consent_152.
 * ПДн 152-ФЗ: форма сайта требует явного согласия; Telegram-ник хэшируется SHA-256 для дедупликации.
 * Подключение: в _leadDoPost добавить ветку  if (p.t === 'b2b_onboarding') return b2bOnboarding(p);
 */
var B2B_ONBOARD_SHEET = 'B2B_Менеджеры';

function _sha256hex(s) {
  var raw = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(s || ''), Utilities.Charset.UTF_8);
  return raw.map(function(b){ return ('0' + (b & 0xff).toString(16)).slice(-2); }).join('');
}

function b2bOnboarding(p) {
  var res = { status: 'ok', details: [] };
  try {
    var name = String(p && p.name || '').trim();
    var salon = String(p && p.salon || '').trim();
    var city = String(p && p.city || '').trim();
    var tg = String(p && p.tg || '').trim().replace(/^@/, '');
    var startId = String(p && p.start_id || '').trim();
    if (!name) return { status: 'error', details: [{ field: 'name', msg: 'нет имени' }] };
    if (!salon) return { status: 'error', details: [{ field: 'salon', msg: 'нет названия салона' }] };
    if (!/^[a-zA-Z0-9_]{4,32}$/.test(tg)) return { status: 'error', details: [{ field: 'tg', msg: 'telegram nick invalid' }] };
    if (p && p.consent !== true) return { status: 'error', details: [{ field: 'consent', msg: 'нет согласия на обработку ПДн (152-ФЗ)' }] };

    var hash = _sha256hex(tg.toLowerCase());
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName(B2B_ONBOARD_SHEET) || ss.insertSheet(B2B_ONBOARD_SHEET);
    if (sh.getLastRow() === 0) sh.appendRow(['ts','start_id','name','salon','city','telegram','status','hash_tg','consent_152']);
    var n = sh.getLastRow();
    if (n > 1) {
      var hashes = sh.getRange(2, 8, n - 1, 1).getValues();
      for (var i = 0; i < hashes.length; i++) {
        if (hashes[i][0] === hash) {
          res.status = 'already'; res.details.push({ step: 'dedup', note: 'менеджер уже в базе' });
          return res;
        }
      }
    }
    sh.appendRow([new Date().toISOString(), startId, name, salon, city, tg, 'enrolled', hash, true]);
    res.details.push({ step: 'enroll', start_id: startId, salon: salon });
    try { console.log('b2b_onboarding', { start_id: startId, salon: salon, city: city }); } catch (e) {}
    return res;
  } catch (e) {
    return { status: 'error', details: [{ step: 'fatal', msg: String(e) }] };
  }
}

/** DEMO для запуска кнопкой Run в редакторе. */
function demoB2BOnboarding() {
  Logger.log('кейс 1 (корректный): ' + JSON.stringify(b2bOnboarding({ name: 'Демо Менеджер', salon: 'Демо-Салон', city: 'Москва', tg: 'demo_manager', consent: true, start_id: 'DEMO-01' })));
  Logger.log('кейс 2 (без согласия — ожидается error): ' + JSON.stringify(b2bOnboarding({ name: 'X', salon: 'X', city: 'X', tg: 'x1', consent: false })));
  Logger.log('кейс 3 (повтор кейса 1 — ожидается already): ' + JSON.stringify(b2bOnboarding({ name: 'Демо Менеджер', salon: 'Демо-Салон', city: 'Москва', tg: 'demo_manager', consent: true, start_id: 'DEMO-01' })));
  Logger.log('После прогона: в таблице появится лист B2B_Менеджеры с 1 строкой.');
}
