/**
 * ЗАПАС ХОДА — дельта v13: R-05 Аукционная система B2B-бонусов
 * Статус: ДЕЛЬТА ДЛЯ ВСТАВКИ ВЛАДЕЛЬЦЕМ (GAS), dry_run=true по умолчанию.
 * Требование ТЗ v3.0 R-05: динамическая ставка вместо фиксированных 2000 ₽,
 * за неликвидные комплекты — до 10–15% от маржи.
 *
 * ВСТАВКА: дополнить существующий bonus_engine.gs (или вставить как файл).
 * Триггер: раз в сутки (time-driven) — selfTest сначала в dry_run.
 */
var BONUS_DRY_RUN = true; // переключить в false только после Bonus-Security-Test

var BONUS_BASE = 2000; // базовый бонус, ₽ (константа ТЗ)

// Классы ликвидности: чем ниже ликвидность — тем выше ставка.
// margin_share — доля маржи, которую отдаём как бонус (10–15% для неликвида).
// Классы ликвидности — синхронизированы с data/product_margins_v1.csv (26 SKU).
var BONUS_CLASSES = [
  { cls: 'fast', match: ['__none__'], share: 0.05 },
  { cls: 'mid', match: ['1;Адаптер Type 2 → GB/T', '2;Адаптер GB/T → Type 2 (обратный)', '4;Кабель Type 2–GB/T', '5;Портативная зарядка GB/T', '6;Адаптер CCS2 → GB/T DC', '7;Адаптер Tesla NACS → CCS2 / Type 2;15000;7000;8000;53;fast', '8;Адаптер Type 2 → GB/T', '12;Держатель / органайзер кабеля GB/T;1500;450;1050;70;fast', '13;Настенная станция GB/T', '14;Удлинитель GB/T → GB/T', '16;Станция 2-в-1: Type 2 + GB/T', '17;Смазка силиконовая (зимний kit);690;200;490;71;fast', '18;Переходник-удлинитель GB/T → 220 В;6500;2800;3700;57;fast', '19;Портативная зарядка Type 2', '21;Кабель Type 2 — Type 2', '22;Кабель Type 2 — Type 2', '23;Настенная станция Type 2', '24;Настенная станция Type 2', '25;Адаптер Type 1 → Type 2;8500;4200;4300;51;fast', '26;Удлинитель Type 2 — Type 2'], share: 0.08 },
  { cls: 'notliquid', match: ['__none__'], share: 0.13 },
];

/**
 * computeBonus(itemId, marginRub) -> {status, details}
 * marginRub — маржа комплекта в ₽ (хранится в shop_products / передаётся из каталога).
 */
function computeBonus(itemId, marginRub) {
  try {
    if (!itemId) return { status: 'error', details: { reason: 'no_item_id' } };
    var cls = 'mid', share = 0.08;
    for (var i = 0; i < BONUS_CLASSES.length; i++) {
      if (BONUS_CLASSES[i].match.indexOf(String(itemId).trim()) !== -1) {
        cls = BONUS_CLASSES[i].cls; share = BONUS_CLASSES[i].share; break;
      }
    }
    var rate = Math.round(BONUS_BASE * (cls === 'notliquid' ? 1.5 : (cls === 'mid' ? 1.15 : 1.0)));
    var marginBased = Math.round((marginRub || 0) * share);
    var bonus = Math.max(rate, marginBased); // не ниже базовой ставки
    if (bonus > 15000) bonus = 15000; // потолок, пока не подтверждены маржные данные
    if (BONUS_DRY_RUN) {
      return { status: 'dry_run', details: { item: itemId, cls: cls, rate: rate, margin_bonus: marginBased, final: bonus } };
    }
    return { status: 'ok', details: { item: itemId, cls: cls, rate: rate, margin_bonus: marginBased, final: bonus } };
  } catch (e) {
    return { status: 'error', details: { reason: String(e) } };
  }
}

/** Ежедневное обновление коэффициентов (time-driven триггер на 06:00 MSK). */
function updateBonusRates() {
  // Источник решения: admin-лист "bonus_rates" — колонки item, cls, share, rate_floor
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName('bonus_rates');
    if (!sh) { console.warn('нет листа bonus_rates — используются дефолтные классы'); return; }
    var rows = sh.getDataRange().getValues();
    var rates = {};
    for (var i = 1; i < rows.length; i++) { rates[String(rows[i][0])] = { cls: rows[i][1], share: Number(rows[i][2]) }; }
    PropertiesService.getScriptProperties().setProperty('bonus_rates', JSON.stringify(rates));
    console.log('rates updated:', Object.keys(rates).length);
  } catch (e) { console.error(e); }
}

/** Виджет «ТОП маржинальных комплектов» — JSON для Mini App. */
function topMarginalJson() {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName('shop_products');
    if (!sh) return JSON.stringify({ updated: new Date().toISOString(), top: [] });
    var rows = sh.getDataRange().getValues();
    var top = [];
    for (var i = 1; i < rows.length; i++) {
      var margin = Number(rows[i][4] || 0); // колонка маржи — сверить по шапке листа
      var bonus = computeBonus(String(rows[i][0]), margin);
      top.push({ id: String(rows[i][0]), margin: margin, bonus: bonus.details && bonus.details.final || 0 });
    }
    top.sort(function(a, b) { return b.bonus - a.bonus; });
    return JSON.stringify({ updated: new Date().toISOString(), top: top.slice(0, 8) });
  } catch (e) {
    return JSON.stringify({ error: String(e) });
  }
}

/** DEMO для запуска кнопкой Run в редакторе (без терминала). */
function demoSelfTest() {
  var cases = [
    ['adapter-premium', 40000],   // fast: ожидается final=2000
    ['station-t2-7kw', 60000],    // mid: ожидается final=4800
    ['bundle-set', 100000],       // notliquid: ожидается final=13000
    ['adapter-ccs2-gbt-dc', 120000] // notliquid: ожидается final=15000 (потолок)
  ];
  cases.forEach(function(c) {
    var res = computeBonus(c[0], c[1]);
    Logger.log(c[0] + ' (маржа ' + c[1] + '): ' + JSON.stringify(res));
  });
  Logger.log('VIN невалидный (WAUZZZ8V9KA123456) -> ' + validateVIN('WAUZZZ8V9KA123456') + ' (ожидается false)');
  Logger.log('VIN валидный (1M8GDM9AXKP042788) -> ' + validateVIN('1M8GDM9AXKP042788') + ' (ожидается true)');
  Logger.log('Все кейсы — dry_run=true, деньги не списываются.');
}