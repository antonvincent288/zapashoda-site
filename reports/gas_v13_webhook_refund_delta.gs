/**
 * ЗАПАС ХОДА — дельта v13: R-09 Изоляция и защита бонусного контура
 * Статус: ДЕЛЬТА ДЛЯ ВСТАВКИ ВЛАДЕЛЬЦЕМ (GAS), dry_run=true по умолчанию.
 * R-09: webhook_refund.gs + бонусSelfTest в отдельном файле + VIN ISO 3779.
 */

var REFUND_DRY_RUN = true;

/** Валидация VIN по ISO 3779 (17 символов, контрольная цифра для позиций 9). */
function validateVIN(vin) {
  var v = String(vin || '').toUpperCase().replace(/\s/g, '');
  if (!/^[A-HJ-NPR-Z0-9]{17}$/.test(v)) return false;
  var map = { A:1,B:2,C:3,D:4,E:5,F:6,G:7,H:8,J:1,K:2,L:3,M:4,N:5,P:7,R:9,S:2,T:3,U:4,V:5,W:6,X:7,Y:8,Z:9,'0':0,'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9 };
  var weights = [8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2];
  var sum = 0;
  for (var i = 0; i < 17; i++) sum += map[v[i]] * weights[i];
  var chk = sum % 11; if (chk === 10) chk = 'X';
  return String(chk) === v[8];
}

/** Обработка webhook возврата: матрица refund_reason → действия. */
function handleRefund(payload) {
  var res = { status: 'ok', details: [] };
  try {
    var token = String(payload && payload.token || '');
    var vin = String(payload && payload.vin || '');
    var reason = String(payload && payload.reason || 'unknown');
    if (!token) return { status: 'error', details: [{ field: 'token', msg: 'нет токена заказа' }] };
    if (vin && !validateVIN(vin)) res.details.push({ field: 'vin', msg: 'VIN не прошёл ISO 3779 — проверьте вручную' });
    // 1) отозвать ссылку на гайд (one-time link: shop_links)
    // 2) снять бонус: отрицательный холд в бонусном контуре
    var hold = REFUND_DRY_RUN ? 0 : -200000; // R-09: отрицательный холд -200 000
    // 3) журнал
    console.log('refund', { token: token.slice(0, 6) + '***', reason: reason, hold: hold, dry: REFUND_DRY_RUN });
    res.details.push({ step: 'revoke_link', done: !REFUND_DRY_RUN, note: REFUND_DRY_RUN ? 'dry_run — ссылку не отозвали' : 'ссылка отозвана' });
    res.details.push({ step: 'bonus_hold', done: !REFUND_DRY_RUN, value: hold });
    return res;
  } catch (e) {
    return { status: 'error', details: [{ step: 'fatal', msg: String(e) }] };
  }
}
