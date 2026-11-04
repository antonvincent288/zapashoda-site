/**
 * ЗАПАС ХОДА — дельта v14: Волна 1.9 UGC «Я выжил на трассе»
 * Статус: ДЕЛЬТА ДЛЯ ВСТАВКИ ВЛАДЕЛЬЦЕМ (GAS). На сайт пока НЕ публикуем —
 * это склад данных «Зала славы» (лист verified_survivors).
 *
 * 1) Создать Google Form: поля — Трасса (М-4/М-11/М-12/другая), Модель и год,
 *    Месяц поездки, Минимальный остаток заряда (%) , Была ли «зона смерти»
 *    (да/нет), Работавшие сети (текст), Фото/скрин (файл, опционально),
 *    Согласие на публикацию (чекбокс), Контакт (телефон/ТГ).
 * 2) В ответах формы настроить «Отправить ответы в» → Apps Script Web App
 *    (или связать форму с таблицей, где лежит этот скрипт).
 * 3) Лист verified_survivors создаётся автоматически.
 */

var UGC_DRY_RUN = true; // склад пишет всегда, публикация на сайт — отдельная волна

function ugcOnSubmit(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName('verified_survivors');
    if (!sh) {
      sh = ss.insertSheet('verified_survivors');
      sh.appendRow(['ts', 'route', 'model', 'month', 'min_soc', 'death_zone', 'networks', 'has_photo', 'consent', 'contact', 'verified']);
    }
    // e.namedValues приходит из формы
    var nv = (e && e.namedValues) || {};
    var g = function(k) { return (nv[k] && nv[k][0]) || ''; };
    var hasPhoto = g('Фото/скрин') !== '';
    var consent = String(g('Согласие на публикацию')).toLowerCase().indexOf('да') !== -1;
    sh.appendRow([
      new Date().toISOString(),
      g('Трасса'), g('Модель и год'), g('Месяц поездки'),
      g('Минимальный остаток заряда (%)'), g('Была ли «зона смерти»'),
      g('Работавшие сети'), hasPhoto ? 'yes' : 'no', consent ? 'yes' : 'no',
      g('Контакт'), 'auto'
    ]);
    console.log('ugc: appended');
    return { status: 'ok', details: { stored: true, dry_run: UGC_DRY_RUN } };
  } catch (err) {
    console.error(err);
    return { status: 'error', details: { msg: String(err) } };
  }
}

/** Web App: приём JSON-отчётов напрямую из Mini App / TG (будущее). */
function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents || '{}');
    var res = ugcOnSubmit({ namedValues: {
      'Трасса': [body.route || ''], 'Модель и год': [body.model || ''],
      'Месяц поездки': [body.month || ''], 'Минимальный остаток заряда (%)': [String(body.min_soc || '')],
      'Была ли «зона смерти»': [body.death_zone || ''], 'Работавшие сети': [body.networks || ''],
      'Фото/скрин': [body.photo ? 'attached' : ''],
      'Согласие на публикацию': [body.consent ? 'да' : ''],
      'Контакт': [body.contact || '']
    }});
    return ContentService.createTextOutput(JSON.stringify(res)).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', details: [{ msg: String(err) }] }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
