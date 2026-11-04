/**
 * SC-MATRIX GENERATOR (Волна 1.6, задача SC-01) — заготовка под динамические VIN-лендинги (R-01).
 *
 * ЧТО ДЕЛАЕТ:
 *  - читает CSV, выгруженный владельцем из Search Console вручную
 *    (Query + Impressions + Clicks + Position; колонка Запрос — первая);
 *  - сопоставляет каждый запрос моделям/брендам каталога zapashoda;
 *  - складывает матрицу в лист sc_matrix: запрос | модель | показы | клики | позиция | тип;
 *  - запускается вручную: generateScMatrix().
 *
 * ПОДГОТОВКА:
 *  1. Search Console → Результаты поиска → Экспорт (CSV) → файл переименовать в sc_export.csv.
 *  2. Положить файл в корень Google Drive (или рядом с таблицей — любой путь, ищем по имени).
 *  3. Создать Таблицу «zapashoda-seo», Extensions → Apps Script → вставить этот файл.
 *  4. Запустить generateScMatrix() (при первом запуске дать разрешения Drive/Sheets).
 */

var SC_CSV_NAME = 'sc_export.csv';
var MATRIX_SHEET = 'sc_matrix';

// Справочник брендов/моделей (пополнять по каталогу; в конце — правки у Алисы)
var KNOWN = [
  ['zeekr', 'Zeekr'], ['зикр', 'Zeekr'],
  ['li auto', 'Li Auto'], ['ли айто', 'Li Auto'], ['лисян', 'Li Auto'], ['lixiang', 'Li Auto'],
  ['voyah', 'Voyah'], ['воях', 'Voyah'],
  ['xiaomi', 'Xiaomi'], ['сяоми', 'Xiaomi'],
  ['byd', 'BYD'],
  ['tesla', 'Tesla'], ['тесла', 'Tesla'],
  ['geely', 'Geely'], ['джили', 'Geely'],
  ['moskvich', 'Moskvich'], ['москвич', 'Moskvich'],
  ['avatr', 'Avatr'], ['аватар', 'Avatr'],
  ['aito', 'Aito'], ['аито', 'Aito'],
  ['omoda', 'Omoda'], ['omodа', 'Omoda'],
  ['changan', 'Changan'], ['чанган', 'Changan'],
  ['haval', 'Haval'], ['хавал', 'Haval'],
  ['chery', 'Chery'], ['черри', 'Chery'],
  ['001', 'Zeekr 001'], ['007', 'Zeekr 007'], ['7x', 'Zeekr 7X'],
  ['l6', 'Li Auto L6'], ['l7', 'Li Auto L7'], ['l9', 'Li Auto L9'],
  ['model 3', 'Tesla Model 3'], ['model y', 'Tesla Model Y'],
  ['su7', 'Xiaomi SU7'], ['ex5', 'Geely EX5'],
  ['song plus', 'BYD Song Plus EV'], ['yuan', 'BYD Yuan Plus']
];

function classifyQuery(q) {
  var ql = String(q || '').toLowerCase();
  var models = [];
  for (var i = 0; i < KNOWN.length; i++) {
    var key = KNOWN[i][0], name = KNOWN[i][1];
    if (ql.indexOf(key) !== -1 && models.indexOf(name) === -1) models.push(name);
  }
  return models;
}

function generateScMatrix() {
  var files = DriveApp.getFilesByName(SC_CSV_NAME);
  if (!files.hasNext()) { Logger.log('Нет файла ' + SC_CSV_NAME + ' в Drive'); return; }
  var csv = Utilities.parseCsv(files.next().getBlob().getDataAsString('UTF-8'));
  if (csv.length < 2) { Logger.log('CSV пуст или без строк'); return; }

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(MATRIX_SHEET) || ss.insertSheet(MATRIX_SHEET);
  sh.clear();
  sh.appendRow(['запрос', 'модель(ы)', 'показы', 'клики', 'позиция', 'тип матрицы']);

  // колонки Search Console: Query, Impressions, Clicks, CTR, Position (обычно 1..5)
  var rows = [];
  for (var i = 1; i < csv.length; i++) {
    var r = csv[i];
    if (!r || !r[0]) continue;
    var q = r[0], impr = parseInt(r[1] || '0', 10) || 0, clicks = parseInt(r[2] || '0', 10) || 0;
    var pos = parseFloat(String(r[4] || r[3] || '').replace(',', '.')) || 0;
    var models = classifyQuery(q);
    if (models.length === 0) rows.push([q, '(общее)', impr, clicks, pos, 'general']);
    else for (var j = 0; j < models.length; j++) rows.push([q, models[j], impr, clicks, pos, 'model']);
  }
  rows.sort(function (a, b) { return (b[2] || 0) - (a[2] || 0); });
  if (rows.length) sh.getRange(2, 1, rows.length, 6).setValues(rows);
  Logger.log('Матрица собрана: ' + rows.length + ' строк (модельных: ' + rows.filter(function (r) { return r[5] === 'model'; }).length + ')');
}
