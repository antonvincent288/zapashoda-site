/**
 * ЗАПАС ХОДА — дельта v16: RELEASE M-11 / M-12 / ЖК-паркинг.
 * 1) doPost переопределён: добавлена ветка t='b2b_onboarding' (v15) — поверх v11.
 * 2) _shopDownload переопределён: выдаёт PDF ПО ПРОДУКТУ из заказа (SHOP_PDF_<SLUG>), не только M4DON.
 * ВСТАВКА: отдельным файлом в том же GAS-проекте (после v11/v12/v13/v15). Объявления функций в этом
 * файле переопределяют одноимённые из v11 — ничего в v11 править не нужно.
 * PDF в Drive: владелец загружает 3 файла и прописывает в Свойствах скрипта:
 *   SHOP_PDF_M11_TRASSA=<fileId>, SHOP_PDF_M12_TRASSA=<fileId>, SHOP_PDF_PARKING_ZHIL=<fileId>
 * (fileId — из URL файла в Drive: docs.google.com/document/d/<FILE_ID>/edit — или /file/d/<FILE_ID>/view)
 */
function doPost(e) {
  try {
    e = e || {};
    if (!e.postData || !e.postData.contents) return _leadDoPost(e);
    let d;
    const _pdC = String(e.postData.contents);
    if (_pdC.trim().indexOf('{') === 0) {
      d = JSON.parse(_pdC);
      if (String(d.t || '') === 'shop_init') return _shopInit(d);
      if (String(d.t || '') === 'b2b_onboarding') return b2bOnboarding(d);
    } else {
      d = {};
      _pdC.split('&').forEach(function (kv) {
        const j2 = kv.indexOf('=');
        if (j2 < 0) return;
        const k2 = decodeURIComponent(kv.slice(0, j2).replace(/\+/g, ' '));
        d[k2] = decodeURIComponent(kv.slice(j2 + 1).replace(/\+/g, ' '));
      });
      if (d.NotificationType || (d.OrderId && d.Status && d.TerminalKey && d.Token)) return _shopNotification(d);
      if (String(d.t || '') === 'shop_init') return _shopInit(d);
      if (String(d.t || '') === 'b2b_onboarding') return b2bOnboarding(d);
    }
    var act = String(d.action || '');
    if (act === 'register') return _userRegister(d);
    if (act === 'login') return _userLogin(d);
    if (d.thread !== undefined && d.thread !== null && String(d.thread) !== '') return _forumDoPost(e, d);
    return _leadDoPost(e);
  } catch (err) {
    return _leadDoPost(e);
  }
}

function _shopDownload(token) {
  token = String(token || '').trim();
  const sh = _shopSheet();
  const last = sh.getLastRow();
  let row = 0;
  if (last > 1) {
    const vals = sh.getRange(2, 1, last - 1, 1).getValues();
    for (let i = 0; i < vals.length; i++) if (String(vals[i][8] || '') === token) { row = i + 2; break; }
  }
  if (!row) return HtmlService.createHtmlOutput(
    '<h2>Ссылка недействительна</h2><p>Токен не найден. Запросите повторную выдачу в поддержке zapashoda-ev.ru.</p>').setTitle('Ссылка недействительна');
  const rv = sh.getRange(row, 1, 1, SHOP_ORDERS_HEADERS.length).getValues()[0];
  const uses = Number(rv[10]) || 0;
  const issued = (rv[9] instanceof Date) ? rv[9].getTime() : (Date.parse(rv[9]) || 0);
  if (uses >= SHOP_TOKEN_MAX_USES) return HtmlService.createHtmlOutput(
    '<h2>Лимит скачиваний исчерпан (' + SHOP_TOKEN_MAX_USES + ')</h2><p>PDF также отправлен на ваш email при оплате. Нужна повторная выдача — напишите в поддержку zapashoda-ev.ru.</p>').setTitle('Лимит исчерпан');
  if (issued && (Date.now() - issued) >= SHOP_TOKEN_TTL_HOURS * 3600 * 1000) return HtmlService.createHtmlOutput(
    '<h2>Срок действия ссылки истёк (' + SHOP_TOKEN_TTL_HOURS + ' ч)</h2><p>PDF отправлен на ваш email при оплате. Нужна повторная выдача — напишите в поддержку zapashoda-ev.ru.</p>').setTitle('Срок истёк');
  const product = String(rv[4] || 'm4don').trim();
  const sp = PropertiesService.getScriptProperties();
  const fileId = sp.getProperty('SHOP_PDF_' + product.toUpperCase()) || sp.getProperty('SHOP_PDF_M4DON');
  if (!fileId) return HtmlService.createHtmlOutput(
    '<h2>Файл ещё не подключён</h2><p>Токен жив, но файл гайда ещё не загружен — повторите попытку позже или напишите в поддержку zapashoda-ev.ru.</p>').setTitle('Файл ещё не подключён');
  const email = String(rv[3] || '');
  const phone = String(rv[4] || '');
  const b64 = Utilities.base64Encode(DriveApp.getFileById(fileId).getBlob().getBytes());
  return _shopWatermarkPdf(b64, email, phone).then(function (wm) {
    if (!wm.watermarked) tgSend('⚠️ SHOP: водяной знак не нанесён (' + String(wm.why || '?') + '). PDF выдан без штампа.');
    sh.getRange(row, 11).setValue(uses + 1);
    return HtmlService.createHtmlOutput(
      '<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
      + '<title>Гайд «Запас хода» — скачивание</title></head>'
      + '<body style="font-family:system-ui,sans-serif;text-align:center;padding-top:48px">'
      + '<h2>Спасибо за покупку 🎉</h2><p>Файл скачивается автоматически. Если нет — нажмите кнопку.</p>'
      + '<a id="dl" download="guide-' + product + '.pdf" style="display:inline-block;margin:16px;padding:12px 22px;border-radius:12px;background:#1fbf7a;color:#fff;text-decoration:none">Скачать PDF</a>'
      + '<p style="color:#777;font-size:12px">Ссылка действует ' + SHOP_TOKEN_TTL_HOURS + ' ч и до ' + SHOP_TOKEN_MAX_USES + ' скачиваний.</p>'
      + '<script>document.getElementById("dl").href="data:application/pdf;base64,' + wm.b64 + '";'
      + 'var a=document.createElement("a");a.href=document.getElementById("dl").href;a.download="guide-' + product + '.pdf";document.body.appendChild(a);a.click();</script>'
      + '</body></html>').setTitle('Гайд «Запас хода»');
  });
}
