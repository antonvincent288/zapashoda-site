/**
 * UGC-COLLECTOR (Волна 1.6, задача UGC-01) — честный склад историй «Выживших».
 *
 * ЧТО ДЕЛАЕТ:
 *  - слушает отправку Google Forms (триггер onFormSubmit);
 *  - валидирует заявку: текст не пустой (>= 40 симв.), ссылок в тексте <= 3 (анти-спам),
 *    приложено фото (обязательно);
 *  - валидные заявки складывает в лист verified_survivors;
 *  - отфильтрованные — в лист rejected с причиной;
 *  - НА САЙТ НИЧЕГО НЕ ПУБЛИКУЕТ. Публикация «Зала славы» — отдельный ручной шаг владельца.
 *
 * УСТАНОВКА (владелец, 5 минут):
 *  1. Google Forms → создать форму «История выжившего» с полями:
 *       - «Текст истории» (абзац текста, обязательно);
 *       - «Фото или скриншот» (загрузка файла, обязательно);
 *       - «Модель авто» (короткий ответ, необязательно);
 *       - «Трасса или место» (короткий ответ, необязательно).
 *  2. В форме: три точки → Apps Script → вставить этот файл целиком.
 *  3. Вписать SPREADSHEET_ID ниже (Google Таблица, где появятся листы).
 *  4. Триггер: иконка «Часики» → Add Trigger → ugcOnFormSubmit → From spreadsheet → On form submit.
 *  5. Прогнать testSetup() один раз — проверит связку.
 */

var SPREADSHEET_ID = ''; // TODO: вставить ID таблицы владельца
var MIN_TEXT = 40;       // минимальная длина истории, символы
var MAX_LINKS = 3;       // максимум ссылок в тексте (анти-спам)

function ugcOnFormSubmit(e) {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var ver = ss.getSheetByName('verified_survivors') || ss.insertSheet('verified_survivors');
  var rej = ss.getSheetByName('rejected') || ss.insertSheet('rejected');
  if (ver.getLastRow() === 0) ver.appendRow(['timestamp','text','photo_url','photo_ids','model','place']);
  if (rej.getLastRow() === 0) rej.appendRow(['timestamp','reason','text_head','has_photo']);

  var items = e.response.getItemResponses();
  var text = '', model = '', place = '', photo = null;
  for (var i = 0; i < items.length; i++) {
    var it = items[i].getItem();
    var title = (it.getTitle() || '').toLowerCase();
    var val = items[i].getResponse();
    if (title.indexOf('истори') !== -1 || title.indexOf('текст') !== -1) text = String(val || '').trim();
    else if (title.indexOf('фото') !== -1 || title.indexOf('скрин') !== -1) photo = val;
    else if (title.indexOf('модель') !== -1) model = String(val || '').trim();
    else if (title.indexOf('трасс') !== -1 || title.indexOf('место') !== -1) place = String(val || '').trim();
  }

  var ts = e.response.getTimestamp();
  // --- валидация ---
  var reasons = [];
  if (!text || text.length < MIN_TEXT) reasons.push('текст пустой или короче ' + MIN_TEXT + ' символов');
  var links = (text.match(/https?:\/\//g) || []).length;
  if (links > MAX_LINKS) reasons.push('спам-подозрение: ' + links + ' ссылок в тексте');
  var photoInfo = null;
  if (photo) {
    // FileUpload: getResponse() возвращает массив ID файлов Drive (или строку)
    var ids = [];
    if (Array.isArray(photo)) ids = photo;
    else if (typeof photo === 'string' && photo.length > 10) ids = [photo];
    if (ids.length === 0) reasons.push('фото не приложено');
    else {
      var urls = [];
      for (var j = 0; j < ids.length; j++) {
        try { urls.push(DriveApp.getFileById(ids[j]).getUrl()); } catch (err) { urls.push('id:' + ids[j]); }
      }
      photoInfo = { ids: ids, urls: urls };
    }
  } else {
    reasons.push('фото не приложено');
  }

  if (reasons.length > 0) {
    rej.appendRow([ts, reasons.join('; '), text.slice(0, 80), photoInfo ? 'да' : 'нет']);
    return 'rejected';
  }

  ver.appendRow([ts, text,
    photoInfo.urls.join(' , '),
    photoInfo.ids.join(','),
    model, place]);
  return 'verified';
}

/** Разовая проверка установки. Запустить вручную один раз. */
function testSetup() {
  if (!SPREADSHEET_ID) throw new Error('Вставьте SPREADSHEET_ID в константу выше');
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  Logger.log('OK: таблица доступна: ' + ss.getName());
}
