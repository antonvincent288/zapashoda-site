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
var BONUS_CLASSES = [
  { cls: 'fast',     match: ['adapter-premium','adapter-reverse'],       share: 0.05 },
  { cls: 'mid',      match: ['adapter-dc-ccs2','station-t2-7kw'],        share: 0.08 },
  { cls: 'notliquid',match: ['station-2in1','station-gbt7','bundle-set'], share: 0.13 }
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
