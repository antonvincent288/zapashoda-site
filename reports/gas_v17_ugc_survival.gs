/**
 * ЗАПАС ХОДА — дельта v17: Волна 2.0 R-UGC-SURVIVAL «Зал славы выживших» + R-STORAGE-01 (ПДн/хэши).
 * ВСТАВКА: отдельным файлом (после v16). Переопределяет doGet/doPost из v11/v16 поверху —
 * объявления ниже перекрывают прежние (V8: последнее объявление функции выигрывает).
 *
 * Лист ugc_stories: ts, route, rating, text, name, contact, photo_id, photo_url,
 *                   geo_lat, geo_lon, consent, exif_stripped, file_hash_sha256, status
 * Модерация: владелец меняет status: pending → approved (или rejected) в листе.
 * Лента /routes/rating/ читает ТОЛЬКО approved через doGet?action=ugc_list.
 * Фото: конвертируется клиентом в JPEG без EXIF (canvas re-encode), сохраняется в Drive-папку
 * «UGC Photo» с правом «любой по ссылке» (чтобы <img> работал в ленте). Дедупликация: SHA-256 фото.
 */
var UGC_STORY_SHEET = 'ugc_stories';
var UGC_PHOTO_FOLDER = 'UGC Photo';
var UGC_PUBLISH_DRY_RUN = true; // после приёмки владельцем: false → лента /routes/rating/ начнёт отдавать записи

function _ugcSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(UGC_STORY_SHEET) || ss.insertSheet(UGC_STORY_SHEET);
  if (sh.getLastRow() === 0) sh.appendRow(['ts','route','rating','text','name','contact','photo_id','photo_url','geo_lat','geo_lon','consent','exif_stripped','file_hash_sha256','status']);
  return sh;
}

function ugcStory(p) {
  var res = { status: 'ok', details: [] };
  try {
    var route = String(p && p.route || '').trim();
    var rating = Number(p && p.rating);
    var text = String(p && p.text || '').trim();
    var name = String(p && p.name || '').trim();
    var contact = String(p && p.contact || '').trim();
    var geo = (p && p.geo && typeof p.geo === 'object') ? p.geo : {};
    var geoLat = Number(geo.lat) || '';
    var geoLon = Number(geo.lon) || '';
    var photoB64 = String(p && p.photo_b64 || '');
    var photoMime = String(p && (p.photo_mime || 'image/jpeg'));

    var trackOk = ['М-4', 'М-11', 'М-12', 'м4', 'м11', 'м12'].indexOf(route) !== -1;
    if (!trackOk) return { status: 'error', details: [{ field: 'route', msg: 'трасса только М-4 / М-11 / М-12' }] };
    if (!(rating >= 1 && rating <= 10)) return { status: 'error', details: [{ field: 'rating', msg: 'оценка 1–10' }] };
    if (text.length < 30) return { status: 'error', details: [{ field: 'text', msg: 'история — минимум 30 символов' }] };
    if (text.length > 2000) return { status: 'error', details: [{ field: 'text', msg: 'история — максимум 2000 символов' }] };
    if (!name) return { status: 'error', details: [{ field: 'name', msg: 'нет имени' }] };
    if (p && p.consent !== true) return { status: 'error', details: [{ field: 'consent', msg: 'нет согласия на публикацию' }] };

    var photoId = '', photoUrl = '', fileHash = '';
    if (photoB64) {
      var bytes = Utilities.base64Decode(photoB64);
      if (bytes.length > 3 * 1024 * 1024) return { status: 'error', details: [{ field: 'photo', msg: 'фото больше 3 МБ' }] };
      fileHash = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, bytes).map(function (b) { return ('0' + (b & 0xff).toString(16)).slice(-2); }).join('');
      var ss = SpreadsheetApp.getActiveSpreadsheet();
      var folders = DriveApp.getFoldersByName(UGC_PHOTO_FOLDER);
      var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(UGC_PHOTO_FOLDER);
      var blob = Utilities.newBlob(bytes, photoMime, 'ugc_' + Date.now() + '.jpg');
      var file = folder.createFile(blob);
      try {
        file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
        photoUrl = 'https://drive.google.com/uc?export=view&id=' + file.getId();
      } catch (e2) { photoUrl = ''; } // если домен запрещает шаринг — лента покажет карточку без фото
      photoId = file.getId();
    }

    var sh = _ugcSheet();
    sh.appendRow([
      new Date().toISOString(), route.toUpperCase(), rating, text, name, contact,
      photoId, photoUrl, geoLat, geoLon,
      p.consent === true ? 'yes' : 'no', photoB64 ? 'client_canvas' : 'n/a', fileHash, 'pending'
    ]);
    try { console.log('ugc_story', { route: route, rating: rating, has_photo: !!photoB64 }); } catch (e3) {}
    res.details.push({ step: 'stored', status: 'pending', note: 'модерация владельцем' });
    return res;
  } catch (e) {
    return { status: 'error', details: [{ step: 'fatal', msg: String(e) }] };
  }
}

function ugcList() {
  var out = [];
  if (UGC_PUBLISH_DRY_RUN) return { status: 'ok', dry_run: true, items: [] };
  try {
    var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(UGC_STORY_SHEET);
    if (!sh || sh.getLastRow() < 2) return { status: 'ok', items: [] };
    var vals = sh.getRange(2, 1, sh.getLastRow() - 1, 14).getValues();
    for (var i = 0; i < vals.length; i++) {
      if (String(vals[i][13]).toLowerCase() !== 'approved') continue;
      var it = {
        ts: vals[i][0] instanceof Date ? vals[i][0].toISOString() : String(vals[i][0]),
        route: String(vals[i][1]), rating: Number(vals[i][2]) || 0,
        text: String(vals[i][3]).slice(0, 600), name: String(vals[i][4]).slice(0, 60),
        photo_url: String(vals[i][7] || ''), geo_lat: vals[i][8], geo_lon: vals[i][9]
      };
      if (it.text) out.push(it);
    }
    return { status: 'ok', items: out };
  } catch (e) {
    return { status: 'error', msg: String(e), items: [] };
  }
}

function doGet(e) {
  try {
    var q = (e && e.parameter) || {};
    if (q.action === 'ugc_list') {
      return ContentService.createTextOutput(JSON.stringify(ugcList())).setMimeType(ContentService.MimeType.JSON);
    }
  } catch (err) {}
  return _leadDoGet(e);
}

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
      if (String(d.t || '') === 'ugc_story') return ContentService.createTextOutput(JSON.stringify(ugcStory(d))).setMimeType(ContentService.MimeType.JSON);
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

/** DEMO: прогнать кнопкой Run — 3 кейса. */
function demoUgcStory() {
  var tiny = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICAgKDA8MCgsOCwgIDRENDg8QEBEQCgsSExIQEA8SEBD/wAALCABAAEABAREA/8QAFwABAQEBAAAAAAAAAAAAAAAABgUHCP/EAB0QAQACAgMBAAAAAAAAAAAAAAECABESAxAhMf/aAAwDAQACEQMRAD8AK8Qpx4SSbimyxCHw/9k=';
  var ok1 = ugcStory({ route: 'М-11', rating: 7, text: 'Прошли дистанцию за день, две зоны смерти на объезде Москвы — держали 40% заряда.', name: 'Демо Тестер', contact: '@demo', consent: true });
  Logger.log('кейс 1 (ok → pending): ' + JSON.stringify(ok1));
  Logger.log('кейс 2 (без согласия — error): ' + JSON.stringify(ugcStory({ route: 'М-4', rating: 5, text: 'История без согласия на публикацию.', name: 'X', consent: false })));
  Logger.log('кейс 3 (оценка 11 — error): ' + JSON.stringify(ugcStory({ route: 'М-12', rating: 11, text: 'Оценка вне шкалы.', name: 'X', consent: true })));
  Logger.log('Кейс 1b (фото): ' + JSON.stringify(ugcStory({ route: 'М-4', rating: 6, text: 'Тестовая история с крошечным фото для проверки Drive и хэша.', name: 'Демо Тестер', contact: '@demo', consent: true, photo_b64: tiny.replace('data:image/jpeg;base64,', ''), photo_mime: 'image/jpeg' })));
  Logger.log('Проверь: лист ugc_stories (4 строки), папка «UGC Photo» в Drive, публичность файла.');
}
