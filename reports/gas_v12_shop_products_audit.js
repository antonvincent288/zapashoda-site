// ============================================================
// GAS v12 — ДЕЛЬТА К v11 (вставлять В КОНЕЦ кода v11 в Apps Script)
// Боевые решения владельца 03.11.2026:
//  1. Цена КАЖДОГО гайда — 990 ₽ (М-4, М-11, М-12, ЖК-паркинг)
//  2. B2B-бонус менеджеру салона — 2 000 ₽ (B2B_BONUS_RUB)
//  3. Двухэтапный холд: заявка → pending; webhook paid → hold;
//     сверка факта оплаты + валидный VIN → paid; иначе rejected.
//  4. Мульти-продукты: Init берёт сумму из PRODUCTS (Script Properties).
// Установка: вставить код в конец проекта, затем один раз выполнить:
//   shopSetProducts(); bonusSelfTest();
// Проверка: shopSelfTest(true) — должен пройти как раньше + лог бонусов.
// ============================================================

var SHOP_PRODUCTS = {
  'm4don':        { title: 'Гайд М-4 «Дон» — трасса М-4', amount: 99000 },
  'm11-trassa':   { title: 'М-11 «Нева»: зарядка на трассе', amount: 99000 },
  'm12-trassa':   { title: 'М-12 «Восток»: зарядка на трассе', amount: 99000 },
  'parking-zhil': { title: 'Зарядка на парковке ЖК', amount: 99000 }
};

function shopGetProducts() {
  var raw = PropertiesService.getScriptProperties().getProperty('shop_products');
  try { return raw ? JSON.parse(raw) : SHOP_PRODUCTS; } catch (e) { return SHOP_PRODUCTS; }
}
function shopSetProducts() {
  PropertiesService.getScriptProperties().setProperty('shop_products', JSON.stringify(SHOP_PRODUCTS));
  Logger.log('shopSetProducts OK: ' + Object.keys(SHOP_PRODUCTS).join(', '));
}
function shopSetProductPrice(slug, rub) {
  var pr = shopGetProducts();
  if (!pr[slug]) throw new Error('нет продукта: ' + slug);
  pr[slug].amount = Math.round(Number(rub) * 100);
  PropertiesService.getScriptProperties().setProperty('shop_products', JSON.stringify(pr));
  Logger.log('цена ' + slug + ' = ' + rub + ' ₽');
}

// ===== INIT ПО ПРОДУКТУ (заменить в v11 тело ветки t=='shop_init' на вызов) =====
// В _odDoPost: if (p.t === 'shop_init') return _shopInitProducts(p);
function _shopInitProducts(p) {
  var pr = shopGetProducts();
  var prod = pr[p.product] || pr['m4don'];
  var amount = prod.amount; // копейки
  var oid = 'ZSD-' + Utilities.formatDate(new Date(), 'Europe/Moscow', 'yyyyMMdd') + '-' + Math.floor(1000 + Math.random() * 9000);
  var email = String(p.email || '').trim();
  var phone = String(p.phone || '').trim();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email)) return { ok: false, error: 'email invalid' };
  if (!/^\+7\d{10}$/.test(phone)) return { ok: false, error: 'phone invalid' };
  var body = {
    TerminalKey: TERMINAL_KEY(), Amount: amount, OrderId: oid, Description: prod.title,
    SuccessURL: SHOP_SUCCESS_URL, FailURL: SHOP_FAIL_URL, NotificationURL: SHOP_WEBHOOK_URL,
    Receipt: { Email: email, Phone: phone, Taxation: TAXATION,
      Items: [{ Name: prod.title, Price: amount, Quantity: 1, Amount: amount, PaymentObject: PAYMENT_OBJECT, Tax: 'none' }] }
  };
  body.Token = _shopToken(body);
  var res = JSON.parse(UrlFetchApp.fetch(shopApiUrl('Init'), { method: 'post', payload: JSON.stringify(body), muteHttpExceptions: true }));
  if (!res.Success) return { ok: false, error: res.Message || res.Details || 'Init failed' };
  _sheetAppend('Заказы', [[oid, new Date().toISOString(), email, phone, p.product || 'm4don', amount, res.PaymentId || '', 'new']]);
  _tg('💳 Init: ' + oid + ' · ' + prod.title + ' · ' + (amount / 100) + ' ₽');
  return { ok: true, paymentUrl: res.PaymentURL, orderId: oid };
}

// ===== B2B-БОНУС 2 000 ₽: ДВУХЭТАПНЫЙ ХОЛД =====
var B2B_BONUS_RUB = 2000; // константа по решению владельца 03.11
function bonusSelfTest() {
  var sh = _bonusSheet();
  Logger.log('Бонусы: строк=' + sh.getLastRow() + '; бонус=' + B2B_BONUS_RUB + ' ₽; цепочка pending→hold→paid/rejected');
}
function _bonusSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('Бонусы') || ss.insertSheet('Бонусы');
  if (sh.getLastRow() === 0) sh.appendRow(['orderId', 'ts', 'product', 'email', 'ref', 'manager_tg', 'amount_rub', 'status', 'vin', 'verified_by', 'paid_at']);
  return sh;
}
// Этап 1: заявка из Mini App (od_order) → бонус pending. Вызывать из обработчика od_order.
function bonusOnOrder(orderId, product, email, ref, managerTg) {
  var sh = _bonusSheet();
  sh.appendRow([orderId, new Date().toISOString(), product, email, ref || '', managerTg || '', B2B_BONUS_RUB, 'pending', '', '', '']);
  _tg('📌 Бонус PENDING ' + B2B_BONUS_RUB + ' ₽: ' + orderId + ' → менеджер ' + (managerTg || '—'));
}
// Этап 2: webhook T-Банка со статусом paid → бонус hold (заморожен до сверки).
// Вызвать из обработчика вебхука после подтверждения статуса PAID/COnfirmED:
function bonusOnWebhookPaid(orderId) {
  var sh = _bonusSheet();
  var rows = sh.getDataRange().getValues();
  for (var i = 1; i < rows.length; i++) {
    if (rows[i][0] === orderId && String(rows[i][7]) === 'pending') {
      sh.getRange(i + 1, 8).setValue('hold');
      _tg('🔒 Бонус HOLD: ' + orderId + ' — платёж подтверждён, ждём сверку');
      return true;
    }
  }
  return false;
}
// Этап 3: сверка. Формат VIN — жёстко; чек-сумма ISO 3779 — предупреждение (не все производители считают).
function validateVin(v) {
  v = String(v || '').toUpperCase().replace(/\s/g, '');
  if (!/^[A-HJ-NPR-Z0-9]{17}$/.test(v)) return { ok: false, reason: 'не 17 символов или есть I/O/Q' };
  var tr = { A:1,B:2,C:3,D:4,E:5,F:6,G:7,H:8,J:1,K:2,L:3,M:4,N:5,P:7,R:9,S:2,T:3,U:4,V:5,W:6,X:7,Y:8,Z:9 };
  var wts = [8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2];
  var sum = 0;
  for (var i = 0; i < 17; i++) {
    var ch = v[i];
    var val = (ch >= '0' && ch <= '9') ? +ch : tr[ch];
    if (val === undefined) return { ok: false, reason: 'недопустимый символ: ' + ch };
    sum += val * wts[i];
  }
  var chk = sum % 11;
  var expect = (chk === 10) ? 'X' : String(chk);
  return { ok: true, checksumMatch: (v[8] === expect), reason: v[8] === expect ? '' : 'чек-сумма не совпала (может быть нормой для не-US/EU VIN)' };
}
function bonusVerify(orderId, vin) {
  var sh = _bonusSheet();
  var rows = sh.getDataRange().getValues();
  var vinCheck = validateVin(vin);
  for (var i = 1; i < rows.length; i++) {
    if (rows[i][0] === orderId) {
      var st = String(rows[i][7]);
      if (st !== 'hold') { _tg('⚠️ Сверка отклонена: ' + orderId + ' — статус ' + st + ', не hold'); return { ok: false, error: 'статус не hold: ' + st }; }
      if (!vinCheck.ok) {
        sh.getRange(i + 1, 8).setValue('rejected');
        sh.getRange(i + 1, 9).setValue(String(vin || '').slice(0, 40));
        _tg('❌ Бонус REJECTED: ' + orderId + ' — ' + vinCheck.reason);
        return { ok: false, error: vinCheck.reason };
      }
      sh.getRange(i + 1, 8).setValue('paid');
      sh.getRange(i + 1, 9).setValue(vin.toUpperCase());
      sh.getRange(i + 1, 11).setValue(new Date().toISOString());
      _tg('✅ Бонус PAID ' + rows[i][6] + ' ₽: ' + orderId + ' · менеджер ' + rows[i][5] + (vinCheck.checksumMatch ? '' : ' (VIN формат ок, чек-сумма предупреждение)'));
      return { ok: true, checksumMatch: vinCheck.checksumMatch };
    }
  }
  return { ok: false, error: 'заказ не найден в Бонусах' };
}
// Еженедельный отчёт по выплатам: bonusReport() — выполнять вручную/по расписанию после сверки.
function bonusReport() {
  var sh = _bonusSheet();
  var rows = sh.getDataRange().getValues();
  var out = { paid: 0, hold: 0, pending: 0, rejected: 0, sum_rub: 0 };
  for (var i = 1; i < rows.length; i++) {
    var st = String(rows[i][7]);
    out[st] = (out[st] || 0) + 1;
    if (st === 'paid') out.sum_rub += Number(rows[i][6]) || 0;
  }
  _tg('📊 Бонусы: paid=' + out.paid + ' (' + out.sum_rub + ' ₽), hold=' + out.hold + ', pending=' + out.pending + ', rejected=' + out.rejected);
  return out;
}

// ===== HTTP-ЭНДПОИНТ ДЛЯ CRON-МОНИТОРА (GitHub Actions → GAS) =====
// В _odDoPost ДОБАВИТЬ ОДНУ ВЕТКУ (рядом с другими):
//   if (p.t === 'bonus_selftest') return _bonusSelftestEndpoint();
// Эндпоинт только читает состояние (листы/конфиги) — безопасен, изменений не вносит.
function _bonusSelftestEndpoint() {
  try {
    var sh = _bonusSheet();
    var pr = shopGetProducts();
    var keys = Object.keys(pr);
    var all990 = keys.length > 0 && keys.every(function (k) { return pr[k].amount === 99000; });
    var pdfsRaw = PropertiesService.getScriptProperties().getProperty('shop_pdfs') || '{}';
    var pdfs = {};
    try { pdfs = JSON.parse(pdfsRaw); } catch (e) {}
    return { ok: true, selftest: true, products: keys.length, all990: all990,
             bonusRub: B2B_BONUS_RUB, bonusRows: Math.max(0, sh.getLastRow() - 1),
             pdfs: Object.keys(pdfs), version: 'v12' };
  } catch (e) {
    return { ok: false, selftest: true, error: String(e && e.message || e) };
  }
}

// Регистрация PDF (вызывает владелец/ассистент при наличии токена Drive):
//   shopSetPdf2('m11-trassa', 'ID_файла_на_Диске')
// Пишет в shop_pdfs — по этому списку конвейер автоматически включает продукт в Live.
function shopSetPdf2(slug, fileId) {
  var raw = PropertiesService.getScriptProperties().getProperty('shop_pdfs') || '{}';
  var pdfs = {};
  try { pdfs = JSON.parse(raw); } catch (e) {}
  pdfs[slug] = fileId;
  PropertiesService.getScriptProperties().setProperty('shop_pdfs', JSON.stringify(pdfs));
  Logger.log('shop_pdfs: ' + Object.keys(pdfs).join(', '));
}
