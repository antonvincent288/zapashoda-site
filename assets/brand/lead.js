/* Запас хода — система лидов: модалка «В заявку» + квиз «Подбор за 30 секунд» + отправка в Telegram/GAS.
   Конфиг вшивается при сборке перед этим файлом: window.ZS_LEAD_CFG = {token, chat, gas}.
   Если token пуст — заявка уходит на GAS (если gas задан) либо пользователю предлагается Telegram-канал. */
(function(){
var CFG = window.ZS_LEAD_CFG || {};
var TG = CFG.token || '';
var CHAT = CFG.chat || '';
var GAS = CFG.gas || '';
var lastSend = 0;

function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function digits(s){return (s||'').replace(/\D/g,'');}

/* ---------- Общий оверлей ---------- */
var ov = document.createElement('div');
ov.id = 'zs-lead-ov';
ov.style.cssText = 'position:fixed;inset:0;z-index:300;display:none;align-items:flex-end;justify-content:center;background:rgba(0,30,43,.55);backdrop-filter:blur(3px)';
var panel = document.createElement('div');
panel.style.cssText = 'background:#fff;width:100%;max-width:560px;max-height:100dvh;overflow-y:auto;border-radius:18px 18px 0 0;padding:22px 20px calc(20px + env(safe-area-inset-bottom));box-shadow:0 -8px 40px rgba(0,0,0,.25)';
ov.appendChild(panel);
document.body.appendChild(ov);
ov.addEventListener('click', function(e){ if(e.target === ov) closeAll(); });
document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeAll(); });
function closeAll(){ ov.style.display = 'none'; panel.innerHTML = ''; document.body.style.overflow = ''; }

function openPanel(html){
  panel.innerHTML = html;
  panel.scrollTop = 0;
  var wide = window.innerWidth >= 720;
  panel.style.borderRadius = wide ? '18px' : '18px 18px 0 0';
  ov.style.alignItems = wide ? 'center' : 'flex-end';
  ov.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

/* ---------- Валидация ---------- */
function validContact(v){
  v = (v||'').trim();
  if(!v) return 'Укажите телефон или Telegram';
  var d = digits(v);
  if(v.indexOf('@') === 0 || v.toLowerCase().indexOf('t.me') === 0) return '';
  if(d.length === 11 && (d[0] === '7' || d[0] === '8')) return '';
  if(d.length === 10) return '';
  if(d.length >= 11) return '';
  return 'Телефон в формате +7 900 000-00-00 или @telegram';
}
function validName(v){ v=(v||'').trim(); return v.length >= 2 ? '' : 'Укажите имя'; }
function validCity(v){ v=(v||'').trim(); return v.length >= 2 ? '' : 'Укажите город'; }

function fieldErr(input, msg){
  var box = input.closest('.lf-field');
  var err = box && box.querySelector('.lf-err');
  if(err) err.textContent = msg || '';
  input.style.borderColor = msg ? '#e5484d' : '';
  return !msg;
}

/* ---------- Отправка ---------- */
function buildMessage(d, source){
  var m = '🔌 НОВЫЙ ЛИД С САЙТА ЗАПАС ХОДА\n';
  m += '🚩 Источник: ' + source + '\n\n';
  if(d.product) m += '📦 Товар: ' + d.product + (d.price ? ' (' + d.price + ')' : '') + '\n';
  if(d.name) m += '👤 Имя: ' + d.name + '\n';
  if(d.contact) m += '📱 Контакт: ' + d.contact + '\n';
  if(d.city) m += '📍 Город: ' + d.city + '\n';
  if(d.carModel) m += '🚗 Автомобиль: ' + d.carModel + '\n';
  if(d.evType) m += '🔋 Тип авто: ' + d.evType + '\n';
  if(d.location) m += '🏠 Место зарядки: ' + d.location + '\n';
  if(d.power) m += '⚡ Мощность: ' + d.power + '\n';
  if(d.comment) m += '💬 Комментарий: ' + d.comment + '\n';
  if(d.page) m += '🔗 Страница: ' + d.page + '\n';
  return m;
}

function sendLead(d, source, onDone, onFail){
  var now = Date.now();
  if(now - lastSend < 8000){ onFail && onFail('Слишком часто. Подождите несколько секунд.'); return; }
  lastSend = now;
  var okAny = false, need = 2, done = 0, failed = false;
  function fin(){ done++; if(done >= need){ if(okAny) onDone && onDone(); else if(!failed) onFail && onFail(); } }
  var toGAS = fetch(GAS, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'},
    body: JSON.stringify(Object.assign({t:'lead', source:source, page:location.href}, d))})
    .then(function(r){ return r.json(); })
    .then(function(res){ if(res && res.ok) okAny = true; fin(); })
    .catch(function(){ fin(); });
  var toTG = Promise.resolve();
  if(TG && CHAT){
    toTG = fetch('https://api.telegram.org/bot' + TG + '/sendMessage', {method:'POST', mode:'no-cors',
      body: new URLSearchParams({chat_id: CHAT, text: buildMessage(d, source), parse_mode: 'HTML'})})
      .then(function(){ okAny = true; fin(); })
      .catch(function(){ fin(); });
  } else {
    need = 1; fin();
  }
  if(!TG || !CHAT){ need = 1; }
}

/* ---------- Модалка «В заявку» ---------- */
function openLead(product, price, productUrl){
  var cart = product ? product + (price ? ' — ' + price : '') : 'Комплект по вашему подбору';
  openPanel(
    '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">'
    + '<div><div class="q-step" style="font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#0aad0a">Заявка на товар</div>'
    + '<h3 style="margin:6px 0 2px;font-size:19px;line-height:1.3">' + esc(product || 'Комплект зарядных устройств') + '</h3>'
    + (price ? '<div style="font-size:15px;color:#5b6b6d;font-weight:600">' + esc(price) + '</div>' : '') + '</div>'
    + '<button type="button" data-zs-close style="border:none;background:#f0f3f2;border-radius:50%;width:36px;height:36px;font-size:18px;cursor:pointer;flex:0 0 auto">✕</button></div>'
    + '<form id="zs-lead-form" novalidate style="margin-top:14px">'
    + '<input type="text" name="zs_hp" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;height:0;opacity:0">'
    + '<div class="lf-field" style="margin-bottom:12px"><input name="name" placeholder="Ваше имя *" required autocomplete="name" style="width:100%;border:1.5px solid #d9dfe5;border-radius:10px;padding:13px 14px;font-size:16px"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
    + '<div class="lf-field" style="margin-bottom:12px"><input name="contact" placeholder="Телефон или @Telegram *" required autocomplete="tel" inputmode="tel" style="width:100%;border:1.5px solid #d9dfe5;border-radius:10px;padding:13px 14px;font-size:16px"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
    + '<div class="lf-field" style="margin-bottom:12px"><input name="city" placeholder="Ваш город *" required autocomplete="address-level2" style="width:100%;border:1.5px solid #d9dfe5;border-radius:10px;padding:13px 14px;font-size:16px"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
    + '<div class="lf-field" style="margin-bottom:14px"><input name="carModel" placeholder="Модель электромобиля (необязательно)" style="width:100%;border:1.5px solid #d9dfe5;border-radius:10px;padding:13px 14px;font-size:16px"></div>'
    + '<button type="submit" id="zs-lead-send" style="width:100%;background:#0aad0a;color:#fff;border:none;border-radius:12px;padding:15px;font-size:16.5px;font-weight:700;cursor:pointer">Отправить заявку</button>'
    + '<p style="font-size:12.5px;color:#5b6b6d;margin:10px 0 0;text-align:center">Ответим в течение рабочего дня. Оплата дилеру при получении.</p>'
    + '</form>');
  var form = document.getElementById('zs-lead-form');
  form.addEventListener('submit', function(e){
    e.preventDefault();
    if(form.querySelector('[name=zs_hp]').value){ return; } // honeypot
    var n = form.querySelector('[name=name]'), c = form.querySelector('[name=contact]'), ct = form.querySelector('[name=city]'), cm = form.querySelector('[name=carModel]');
    var ok = true;
    ok = fieldErr(n, validName(n.value)) && ok;
    ok = fieldErr(c, validContact(c.value)) && ok;
    ok = fieldErr(ct, validCity(ct.value)) && ok;
    if(!ok) return;
    var btn = document.getElementById('zs-lead-send');
    btn.disabled = true; btn.textContent = 'Отправка…';
    sendLead({
      product: product || '', price: price || '', name: n.value.trim(), contact: c.value.trim(),
      city: ct.value.trim(), carModel: cm.value.trim()
    }, product ? 'Кнопка «В заявку»: ' + product : 'Модалка заявки',
    function(){ showSuccess('✅ Заявка отправлена', 'Менеджер свяжется с вами в ближайшее время и предложит ближайшего дилера.'); },
    function(msg){ showLeadError(btn, msg); });
  });
}

function showLeadError(btn, msg){
  btn.disabled = false; btn.textContent = 'Отправить заявку';
  var box = btn.parentElement.querySelector('.lf-note');
  if(!box){ box = document.createElement('p'); box.className = 'lf-note'; box.style.cssText = 'font-size:13px;color:#e5484d;margin:10px 0 0;text-align:center'; btn.insertAdjacentElement('afterend', box); }
  box.textContent = msg || 'Не удалось отправить. Напишите нам в Telegram: @zapashoda_ev';
}

function showSuccess(h, p){
  openPanel('<div style="text-align:center;padding:26px 6px"><div style="font-size:52px;line-height:1">✅</div>'
    + '<h3 style="font-size:21px;margin:14px 0 6px">' + esc(h) + '</h3>'
    + '<p style="font-size:15px;color:#5b6b6d;margin:0 0 18px">' + esc(p) + '</p>'
    + '<button type="button" data-zs-close style="background:#0aad0a;color:#fff;border:none;border-radius:12px;padding:14px 26px;font-size:16px;font-weight:700;cursor:pointer">Готово</button></div>');
  panel.querySelector('[data-zs-close]').addEventListener('click', closeAll);
}

/* ---------- Квиз «Подбор за 30 секунд» ---------- */
var QUIZ_STEPS = [
  {key:'evType', title:'Выберите тип вашего авто', opts:[
    ['Чистый электромобиль (BEV)', 'Полностью на батарее'],
    ['Подключаемый гибрид (PHEV / EREV)', 'Батарея + двигатель внутреннего сгорания']]},
  {key:'brand', title:'Марка вашего авто', brands:['Zeekr','Li Auto','Voyah','BYD','Tesla','Xiaomi'], free:'Впишите модель (например, Zeekr 001)'},
  {key:'location', title:'Где чаще всего планируете заряжаться?', opts:[
    ['Частный дом / Дача', 'Есть розетка или можно поставить станцию'],
    ['Подземный паркинг в ЖК', 'Нужно согласование УК'],
    ['Обычная уличная парковка / Работа', 'Городские станции']]},
  {key:'power', title:'Какая мощность сети доступна?', opts:[
    ['220В (обычная розетка или 1 фаза до 7 кВт)', 'Медленная зарядка ночью'],
    ['380В (3 фазы до 22 кВт)', 'Быстрая домашняя зарядка'],
    ['Не знаю, нужна консультация', 'Подскажем по фото щитка']]},
];

var quizState = {step:0, answers:{}, mode:'modal'};

function quizSummary(){
  var a = quizState.answers;
  return 'Тип: ' + (a.evType || '—') + ' · Авто: ' + (a.brand || '—') + ' · Зарядка: ' + (a.location || '—') + ' · Сеть: ' + (a.power || '—');
}

function renderQuiz(container){
  var s = quizState.step;
  var html = '';
  if(s < QUIZ_STEPS.length){
    var st = QUIZ_STEPS[s];
    html += '<div class="q-step" style="font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#0aad0a">Шаг ' + (s+1) + ' из ' + QUIZ_STEPS.length + '</div>';
    html += '<div style="height:6px;background:#e7f6ee;border-radius:3px;margin:10px 0 16px"><div style="height:100%;background:#0aad0a;border-radius:3px;width:' + Math.round(((s)/QUIZ_STEPS.length)*100) + '%;transition:width .25s"></div></div>';
    html += '<h3 style="font-size:20px;margin:0 0 14px">' + esc(st.title) + '</h3>';
    if(st.opts){
      st.opts.forEach(function(o){
        var sel = quizState.answers[st.key] === o[0];
        html += '<button type="button" class="zs-qopt" data-v="' + esc(o[0]) + '" style="display:block;width:100%;text-align:left;border:1.5px solid ' + (sel ? '#0aad0a' : '#d9dfe5') + ';background:' + (sel ? '#e7f6ee' : '#fff') + ';border-radius:12px;padding:14px 16px;margin-bottom:10px;cursor:pointer">'
          + '<b style="font-size:15.5px;display:block">' + esc(o[0]) + '</b><span style="font-size:13px;color:#5b6b6d">' + esc(o[1] || '') + '</span></button>';
      });
    }
    if(st.brands){
      html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px">';
      st.brands.forEach(function(b){
        var sel = quizState.answers[st.key] === b;
        html += '<button type="button" class="zs-qopt" data-v="' + esc(b) + '" style="border:1.5px solid ' + (sel ? '#0aad0a' : '#d9dfe5') + ';background:' + (sel ? '#e7f6ee' : '#fff') + ';border-radius:10px;padding:12px 6px;font-weight:700;font-size:14px;cursor:pointer">' + esc(b) + '</button>';
      });
      html += '</div>';
      html += '<input type="text" class="zs-qfree" placeholder="' + esc(st.free) + '" value="' + esc(quizState.answers.freeModel || '') + '" style="width:100%;border:1.5px solid #d9dfe5;border-radius:10px;padding:13px 14px;font-size:16px">';
    }
    html += '<div style="display:flex;gap:10px;margin-top:16px">'
      + (s > 0 ? '<button type="button" class="zs-qback" style="border:1.5px solid #d9dfe5;background:#fff;border-radius:12px;padding:13px 18px;font-size:15px;font-weight:600;cursor:pointer">Назад</button>' : '')
      + (s > 0 ? '' : '')
      + (quizState.answers[st.key] || st.brands ? '<button type="button" class="zs-qnext" style="flex:1;background:#0aad0a;color:#fff;border:none;border-radius:12px;padding:14px;font-size:16px;font-weight:700;cursor:pointer">Далее →</button>' : '')
      + '</div>';
  } else {
    html += '<div class="q-step" style="font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#0aad0a">Финал</div>'
      + '<div style="height:6px;background:#e7f6ee;border-radius:3px;margin:10px 0 16px"><div style="height:100%;background:#0aad0a;border-radius:3px;width:100%"></div></div>'
      + '<h3 style="font-size:20px;margin:0 0 8px">Спасибо! Подобрали комплект под ваш сценарий</h3>'
      + '<p style="font-size:14px;color:#5b6b6d;margin:0 0 6px">' + esc(quizSummary()) + '</p>'
      + '<p style="font-size:14.5px;margin:0 0 14px">Куда прислать расчёт стоимости и контакты ближайшего сертифицированного дилера для установки?</p>'
      + '<form id="zs-quiz-form" novalidate>'
      + '<input type="text" name="zs_hp" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;height:0;opacity:0">'
      + '<div class="lf-field" style="margin-bottom:12px"><input name="name" placeholder="Ваше имя *" required autocomplete="name" style="width:100%;border:1.5px solid #d9dfe5;border-radius:10px;padding:13px 14px;font-size:16px"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
      + '<div class="lf-field" style="margin-bottom:12px"><input name="contact" placeholder="Телефон или @Telegram *" required inputmode="tel" style="width:100%;border:1.5px solid #d9dfe5;border-radius:10px;padding:13px 14px;font-size:16px"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
      + '<div class="lf-field" style="margin-bottom:14px"><input name="city" placeholder="Ваш город *" required autocomplete="address-level2" style="width:100%;border:1.5px solid #d9dfe5;border-radius:10px;padding:13px 14px;font-size:16px"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
      + '<button type="submit" id="zs-quiz-send" style="width:100%;background:#0aad0a;color:#fff;border:none;border-radius:12px;padding:15px;font-size:16.5px;font-weight:700;cursor:pointer">Получить расчёт</button>'
      + '<p style="font-size:12.5px;color:#5b6b6d;margin:10px 0 0;text-align:center">Без звонков-спамеров: один менеджер, один раз.</p>'
      + '</form>'
      + '<button type="button" class="zs-qback" style="background:none;border:none;color:#5b6b6d;font-size:14px;cursor:pointer;margin-top:8px">← Изменить ответы</button>';
  }
  container.innerHTML = html;

  container.querySelectorAll('.zs-qopt').forEach(function(b){
    b.addEventListener('click', function(){
      var st = QUIZ_STEPS[quizState.step];
      quizState.answers[st.key] = b.getAttribute('data-v');
      if(st.key === 'brand') delete quizState.answers.freeModel;
      renderQuiz(container);
      if(st.opts){ var nx = container.querySelector('.zs-qnext'); if(nx) nx.click(); }
    });
  });
  var free = container.querySelector('.zs-qfree');
  if(free) free.addEventListener('input', function(){ quizState.answers.freeModel = free.value.trim(); });
  var back = container.querySelector('.zs-qback');
  if(back) back.addEventListener('click', function(){ quizState.step = Math.max(0, quizState.step - 1); renderQuiz(container); });
  var next = container.querySelector('.zs-qnext');
  if(next) next.addEventListener('click', function(){
    var st = QUIZ_STEPS[quizState.step];
    if(st.brands && !quizState.answers[st.key] && !quizState.answers.freeModel){ next.blur(); return; }
    quizState.step++; renderQuiz(container);
  });
  var qform = container.querySelector('#zs-quiz-form');
  if(qform) qform.addEventListener('submit', function(e){
    e.preventDefault();
    if(qform.querySelector('[name=zs_hp]').value) return;
    var n = qform.querySelector('[name=name]'), c = qform.querySelector('[name=contact]'), ct = qform.querySelector('[name=city]');
    var ok = true;
    ok = fieldErr(n, validName(n.value)) && ok;
    ok = fieldErr(c, validContact(c.value)) && ok;
    ok = fieldErr(ct, validCity(ct.value)) && ok;
    if(!ok) return;
    var btn = qform.querySelector('#zs-quiz-send');
    btn.disabled = true; btn.textContent = 'Отправка…';
    var a = quizState.answers;
    var brandLine = (a.brand || '') + (a.freeModel ? ' ' + a.freeModel : '');
    sendLead({
      evType: a.evType || '', carModel: brandLine, location: a.location || '', power: a.power || '',
      name: n.value.trim(), contact: c.value.trim(), city: ct.value.trim()
    }, 'Квиз «Подбор за 30 секунд»',
    function(){ showSuccess('✅ Расчёт в пути', 'Менеджер соберёт расчёт и пришлёт контакты дилера для установки. Обычно — в течение рабочего дня.'); },
    function(msg){ showLeadError(btn, msg); });
  });
}

function openQuiz(mode){
  quizState = {step:0, answers:{}, mode:mode || 'modal'};
  if(mode === 'inline'){
    var box = document.getElementById('zs-quiz-inline');
    if(!box){ box = document.createElement('div'); box.id = 'zs-quiz-inline'; box.style.cssText = 'max-width:760px;margin:0 auto;padding:0 12px 40px';
      var mainEl = document.querySelector('main');
      if(mainEl && mainEl.parentNode) mainEl.parentNode.insertBefore(box, mainEl); else document.body.appendChild(box); }
    renderQuiz(box);
    var old = document.querySelector('.quiz-wrap');
    if(old) old.style.display = 'none';
    box.scrollIntoView({behavior:'smooth', block:'start'});
    return;
  }
  openPanel('<div style="display:flex;justify-content:flex-end"><button type="button" data-zs-close style="border:none;background:#f0f3f2;border-radius:50%;width:36px;height:36px;font-size:18px;cursor:pointer">✕</button></div><div id="zs-quiz-body"></div>');
  panel.querySelector('[data-zs-close]').addEventListener('click', closeAll);
  renderQuiz(panel.querySelector('#zs-quiz-body'));
}

/* ---------- Перехват кликов ---------- */
document.addEventListener('click', function(e){
  var add = e.target.closest('.sku-add, .pc-add');
  if(add){
    e.preventDefault(); e.stopPropagation();
    var card = add.closest('.card-product') || add.closest('div');
    var root = card && card.closest ? card : add.closest('[data-price]');
    var box = add.closest('[data-price]') || (card && card.querySelector('[data-price]') ? card : add.closest('.rounded-lg'));
    var price = '', name = '';
    var priceEl = box && (box.getAttribute('data-price') || '');
    if(priceEl) price = priceEl.replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' ₽';
    var titleEl = box && box.querySelector('b, h3 a, h3');
    if(titleEl) name = titleEl.textContent.trim();
    if(!name){ var linkEl = box && box.querySelector('a[href*=".html"]'); if(linkEl) name = linkEl.textContent.trim(); }
    if(!name && !price){ var h1 = document.querySelector('h1'); if(h1) name = h1.textContent.trim().replace(/[:.].*$/, ''); }
    var href = box && box.querySelector('a[href*=".html"]');
    openLead(name || '', price || '', href ? href.getAttribute('href') : '');
    return;
  }
  var qa = e.target.closest('a[href="/quiz/"], a[href="' + location.origin + '/quiz/"]');
  if(qa){
    e.preventDefault(); e.stopPropagation();
    var width = window.innerWidth;
    if(location.pathname === '/quiz/' || width < 720){ openQuiz('modal'); }
    else openQuiz('modal');
    return;
  }
  if(e.target.closest('[data-zs-close]')){ closeAll(); }
}, true);

/* На /quiz/ рендерим квиз встроенно */
if(location.pathname === '/quiz/' || location.pathname === '/quiz/index.html'){
  document.addEventListener('DOMContentLoaded', function(){ if(document.readyState !== 'loading') openQuiz('inline'); });
  if(document.readyState !== 'loading') openQuiz('inline');
}
})();
