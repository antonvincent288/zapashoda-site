/* Запас хода — лид-система v2 (проект «№1»): модалка «В заявку» + квиз 30 сек + Telegram/GAS.
   Конфиг вшивается при сборке: window.ZS_LEAD_CFG = {token, chat, gas}. */
(function(){
var CFG = window.ZS_LEAD_CFG || {};
var TG = CFG.token || '';
var CHAT = CFG.chat || '';
var GAS = CFG.gas || '';
var lastSend = 0;
var ACC = '#2563EB', ACC_H = '#1D4ED8', LINE = '#E2E8F0', MUTED = '#64748B';

function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function digits(s){return (s||'').replace(/\D/g,'');}

/* ---------- Оверлей ---------- */
var ov = document.createElement('div');
ov.id = 'zs-lead-ov';
ov.style.cssText = 'position:fixed;inset:0;z-index:1000;display:none;align-items:flex-end;justify-content:center;background:rgba(15,23,42,.6);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px)';
var panel = document.createElement('div');
panel.style.cssText = 'background:#fff;width:100%;max-width:560px;max-height:100dvh;overflow-y:auto;border-radius:16px;padding:24px;box-shadow:0 20px 50px rgba(0,0,0,.3);animation:zsIn .28s cubic-bezier(.4,0,.2,1)';
ov.appendChild(panel);
if(!document.getElementById('zs-lead-style')){
  var st = document.createElement('style'); st.id = 'zs-lead-style';
  st.textContent = '@keyframes zsIn{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}'
    + '@keyframes zsFade{from{opacity:0;transform:translateX(14px)}to{opacity:1;transform:none}}'
    + '.zs-fade{animation:zsFade .26s cubic-bezier(.4,0,.2,1)}'
    + '.lf-field input{width:100%;border:1.5px solid ' + LINE + ';border-radius:12px;padding:14px;font-size:16px;background:#fff;transition:all .25s cubic-bezier(.4,0,.2,1)}'
    + '.lf-field input:focus{outline:none;border-color:' + ACC + ';box-shadow:0 0 0 3px rgba(37,99,235,.14)}'
    + '.zs-btn{width:100%;background:' + ACC + ';color:#fff;border:none;border-radius:12px;padding:15px;font-size:16.5px;font-weight:700;cursor:pointer;transition:all .25s cubic-bezier(.4,0,.2,1)}'
    + '.zs-btn:hover{background:' + ACC_H + '}'
    + '.zs-btn:disabled{opacity:.6;cursor:not-allowed}'
    + '.zs-qopt{display:block;width:100%;text-align:left;border:1.5px solid ' + LINE + ';background:#fff;border-radius:12px;padding:14px 16px;margin-bottom:10px;cursor:pointer;transition:all .25s cubic-bezier(.4,0,.2,1)}'
    + '.zs-qopt:hover{border-color:' + ACC + ';transform:translateY(-1px)}'
    + '.zs-qopt b{font-size:15.5px;display:block}'
    + '.zs-qopt span{font-size:13px;color:' + MUTED + '}';
  document.head.appendChild(st);
}
document.body.appendChild(ov);
ov.addEventListener('click', function(e){ if(e.target === ov) closeAll(); });
document.addEventListener('keydown', function(e){ if(e.key === 'Escape') closeAll(); });
function closeAll(){ ov.style.display = 'none'; panel.innerHTML = ''; document.body.style.overflow = ''; }
function openPanel(html){
  panel.innerHTML = html;
  panel.scrollTop = 0;
  var wide = window.innerWidth >= 720;
  panel.style.borderRadius = wide ? '16px' : '16px 16px 0 0';
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

/* ---------- Формат сообщения (для дилеров) ---------- */
function buildMessage(d, source){
  var L = '───────────────────';
  var m = '🔌 <b>НОВАЯ ЗАЯВКА | ЗАПАС ХОДА</b>\n' + L + '\n';
  m += '📁 Тип: <b>' + esc(source) + '</b>\n';
  m += '👤 Имя: ' + esc(d.name) + '\n';
  m += '📱 Контакт: ' + esc(d.contact) + '\n';
  m += '📍 Город: ' + esc(d.city) + '\n';
  if(d.product){ m += '📦 Товар: <b>' + esc(d.product) + '</b>\n'; m += '💰 Цена: ' + esc(d.price || 'Не указана') + '\n'; }
  if(d.carModel) m += '🚗 Автомобиль: ' + esc(d.carModel) + '\n';
  if(d.quizAnswers){ m += '📊 Сценарий зарядки:\n' + d.quizAnswers + '\n'; }
  if(d.comment) m += '💬 Комментарий: ' + esc(d.comment) + '\n';
  m += L + '\n🔗 ' + (d.page || location.href);
  return m;
}

function sendLead(d, source, onDone, onFail){
  var now = Date.now();
  if(now - lastSend < 8000){ onFail && onFail('Слишком часто. Подождите несколько секунд.'); return; }
  lastSend = now;
  var okAny = false, need = TG && CHAT ? 2 : 1, done = 0;
  function fin(){ done++; if(done >= need){ if(okAny) onDone && onDone(); else onFail && onFail(); } }
  fetch(GAS, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'},
    body: JSON.stringify(Object.assign({t:'lead', source:source, page:location.href}, d))})
    .then(function(r){ return r.json(); })
    .then(function(res){ if(res && res.ok) okAny = true; fin(); })
    .catch(function(){ fin(); });
  if(TG && CHAT){
    fetch('https://api.telegram.org/bot' + TG + '/sendMessage', {method:'POST', mode:'no-cors',
      body: new URLSearchParams({chat_id: CHAT, text: buildMessage(d, source), parse_mode: 'HTML'})})
      .then(function(){ okAny = true; fin(); })
      .catch(function(){ fin(); });
  }
}

/* ---------- Модалка «В заявку» ---------- */
function openLead(product, price, productUrl, model, mode){
  var title = mode === 'b2b' ? 'Запрос оптового прайса' : (product ? 'Оформление заявки на «' + product + '»' : 'Оформление заявки на комплект');
  openPanel(
    '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">'
    + '<div><div class="q-step" style="font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:' + ACC + '">Заявка</div>'
    + '<h3 style="margin:6px 0 2px;font-size:19px;line-height:1.3">' + esc(title) + '</h3>'
    + (price ? '<div style="font-size:15px;color:' + MUTED + ';font-weight:600">' + esc(price) + '</div>' : '') + '</div>'
    + '<button type="button" data-zs-close style="border:none;background:#F1F5F9;border-radius:50%;width:36px;height:36px;font-size:18px;cursor:pointer;flex:0 0 auto">✕</button></div>'
    + '<form id="zs-lead-form" novalidate style="margin-top:14px">'
    + '<input type="text" name="zs_hp" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;height:0;opacity:0">'
    + '<div class="lf-field" style="margin-bottom:12px"><input name="name" placeholder="Ваше имя *" required autocomplete="name"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
    + '<div class="lf-field" style="margin-bottom:12px"><input name="contact" placeholder="Телефон или @Telegram *" required autocomplete="tel" inputmode="tel"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
    + '<div class="lf-field" style="margin-bottom:12px"><input name="city" list="zs-cities" placeholder="Ваш город *" required autocomplete="address-level2"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
    + '<div class="lf-field" style="margin-bottom:14px"><input name="carModel" placeholder="Модель электромобиля (необязательно)"></div>'
    + '<button type="submit" id="zs-lead-send" class="zs-btn">Отправить заявку</button>'
    + '<p style="font-size:12.5px;color:' + MUTED + ';margin:10px 0 0;text-align:center">Ответим в течение рабочего дня. Оплата дилеру при получении.</p>'
    + '</form>');
  var form = document.getElementById('zs-lead-form');
  if(model){ var cmv = form.querySelector('[name=carModel]'); if(cmv && !cmv.value) cmv.value = model; }
  form.addEventListener('submit', function(e){
    e.preventDefault();
    if(form.querySelector('[name=zs_hp]').value){ return; }
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
    }, product ? 'Заказ товара: ' + product : 'Заявка с сайта',
    function(){ showSuccess('✅ Заявка отправлена!', 'Мы свяжемся с вами в ближайшее время и предложим ближайшего дилера.'); },
    function(msg){ showLeadError(btn, msg); });
  });
}

function showLeadError(btn, msg){
  btn.disabled = false; btn.textContent = 'Отправить заявку';
  var box = btn.parentElement.querySelector('.lf-note');
  if(!box){ box = document.createElement('p'); box.className = 'lf-note'; box.style.cssText = 'font-size:13px;color:#e5484d;margin:10px 0 0;text-align:center'; btn.insertAdjacentElement('afterend', box); }
  box.textContent = msg || 'Ошибка при отправке. Пожалуйста, попробуйте позже или напишите нам: @zapashoda_ev';
}

function showSuccess(h, p){
  openPanel('<div class="zs-fade" style="text-align:center;padding:26px 6px"><div style="font-size:52px;line-height:1">✅</div>'
    + '<h3 style="font-size:21px;margin:14px 0 6px">' + esc(h) + '</h3>'
    + '<p style="font-size:15px;color:' + MUTED + ';margin:0 0 18px">' + esc(p) + '</p>'
    + '<button type="button" data-zs-close class="zs-btn" style="max-width:220px;margin:0 auto;display:block">Готово</button></div>');
  panel.querySelector('[data-zs-close]').addEventListener('click', closeAll);
}

/* ---------- Квиз «Подбор за 30 секунд» ---------- */
var QUIZ_STEPS = [
  {key:'evType', title:'Выберите тип вашего авто', opts:[
    ['BEV — Чистый электромобиль', 'Полностью на батарее'],
    ['PHEV — Подключаемый гибрид', 'Батарея + ДВС (EREV)']]},
  {key:'brand', title:'Марка и модель вашего авто', brands:['Zeekr','Li Auto','Voyah','BYD','Tesla','Xiaomi'], free:'Впишите модель (например, Zeekr 001)'},
  {key:'location', title:'Где чаще всего планируете заряжаться?', opts:[
    ['Частный дом / Дача', 'Есть розетка или можно поставить станцию'],
    ['Подземный паркинг в ЖК', 'Нужно согласование УК'],
    ['Уличная парковка / Работа', 'Городские станции']]},
  {key:'power', title:'Какая мощность сети доступна?', opts:[
    ['220В — 1 фаза до 7 кВт', 'Медленная зарядка ночью'],
    ['380В — 3 фазы до 22 кВт', 'Быстрая домашняя зарядка'],
    ['Не знаю, нужна консультация электрика', 'Подскажем по фото щитка']]},
];

var quizState = {step:0, answers:{}, mode:'modal'};

function quizAnswersText(){
  var a = quizState.answers;
  return '   • Тип: ' + (a.evType || '—') + '\n   • Авто: ' + ((a.brand || '') + (a.freeModel ? ' ' + a.freeModel : '') || '—')
    + '\n   • Зарядка: ' + (a.location || '—') + '\n   • Сеть: ' + (a.power || '—');
}

function renderQuiz(container){
  var s = quizState.step;
  var html = '<div class="zs-fade">';
  if(s < QUIZ_STEPS.length){
    var st = QUIZ_STEPS[s];
    var pct = Math.round(((s+1)/(QUIZ_STEPS.length+1))*100);
    html += '<div style="display:flex;justify-content:space-between;align-items:center"><div class="q-step" style="font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:' + ACC + '">Шаг ' + (s+1) + ' из ' + QUIZ_STEPS.length + '</div><div style="font-size:12px;color:' + MUTED + ';font-weight:600">' + pct + '%</div></div>';
    html += '<div style="height:6px;background:#EFF6FF;border-radius:3px;margin:10px 0 16px"><div style="height:100%;background:' + ACC + ';border-radius:3px;width:' + pct + '%;transition:width .3s cubic-bezier(.4,0,.2,1)"></div></div>';
    html += '<h3 style="font-size:20px;margin:0 0 14px">' + esc(st.title) + '</h3>';
    if(st.opts){
      st.opts.forEach(function(o){
        var sel = quizState.answers[st.key] === o[0];
        html += '<button type="button" class="zs-qopt" data-v="' + esc(o[0]) + '" style="border-color:' + (sel ? ACC : LINE) + ';background:' + (sel ? '#EFF6FF' : '#fff') + '">'
          + '<b>' + esc(o[0]) + '</b>' + (o[1] ? '<span>' + esc(o[1]) + '</span>' : '') + '</button>';
      });
    }
    if(st.brands){
      html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px">';
      st.brands.forEach(function(b){
        var sel = quizState.answers[st.key] === b;
        html += '<button type="button" class="zs-qopt" data-v="' + esc(b) + '" style="border-color:' + (sel ? ACC : LINE) + ';background:' + (sel ? '#EFF6FF' : '#fff') + ';padding:12px 6px;font-weight:700;font-size:14px;text-align:center;display:block">' + esc(b) + '</button>';
      });
      html += '</div>';
      html += '<input type="text" class="zs-qfree lf-input" placeholder="' + esc(st.free) + '" value="' + esc(quizState.answers.freeModel || '') + '" style="width:100%;border:1.5px solid ' + LINE + ';border-radius:12px;padding:14px;font-size:16px">';
    }
    html += '<div style="display:flex;gap:10px;margin-top:16px">'
      + (s > 0 ? '<button type="button" class="zs-qback" style="border:1.5px solid ' + LINE + ';background:#fff;border-radius:12px;padding:13px 18px;font-size:15px;font-weight:600;cursor:pointer">Назад</button>' : '')
      + (s > 0 ? '' : '')
      + '<button type="button" class="zs-qnext" style="flex:1;background:' + ACC + ';color:#fff;border:none;border-radius:12px;padding:14px;font-size:16px;font-weight:700;cursor:pointer;transition:all .25s cubic-bezier(.4,0,.2,1)">Далее →</button>'
      + '</div>';
  } else {
    html += '<div style="display:flex;justify-content:space-between;align-items:center"><div class="q-step" style="font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:' + ACC + '">Финал</div><div style="font-size:12px;font-weight:700;color:' + ACC + '">100% Заполнено</div></div>'
      + '<div style="height:6px;background:#EFF6FF;border-radius:3px;margin:10px 0 16px"><div style="height:100%;background:' + ACC + ';border-radius:3px;width:100%"></div></div>'
      + '<h3 style="font-size:20px;margin:0 0 8px">Спасибо! Мы подобрали идеальное решение</h3>'
      + '<p style="font-size:13.5px;color:' + MUTED + ';margin:0 0 10px;white-space:pre-line">' + esc(quizAnswersText().replace(/^   /gm, ' ')) + '</p>'
      + '<p style="font-size:14.5px;margin:0 0 14px">Куда прислать расчёт стоимости и контакты ближайшего сертифицированного дилера для установки?</p>'
      + '<form id="zs-quiz-form" novalidate>'
      + '<input type="text" name="zs_hp" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;height:0;opacity:0">'
      + '<div class="lf-field" style="margin-bottom:12px"><input name="name" placeholder="Ваше имя *" required autocomplete="name"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
      + '<div class="lf-field" style="margin-bottom:12px"><input name="contact" placeholder="Телефон или @Telegram *" required inputmode="tel"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
      + '<div class="lf-field" style="margin-bottom:14px"><input name="city" placeholder="Ваш город *" required autocomplete="address-level2"><div class="lf-err" style="color:#e5484d;font-size:12.5px;margin-top:3px"></div></div>'
      + '<button type="submit" id="zs-quiz-send" class="zs-btn">Получить расчёт</button>'
      + '<p style="font-size:12.5px;color:' + MUTED + ';margin:10px 0 0;text-align:center">Без звонков-спамеров: один менеджер, один раз.</p>'
      + '</form>'
      + '<button type="button" class="zs-qback" style="background:none;border:none;color:' + MUTED + ';font-size:14px;cursor:pointer;margin-top:8px">← Изменить ответы</button>';
  }
  html += '</div>';
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
    sendLead({
      carModel: ((a.brand || '') + (a.freeModel ? ' ' + a.freeModel : '')),
      name: n.value.trim(), contact: c.value.trim(), city: ct.value.trim(),
      quizAnswers: quizAnswersText()
    }, 'Квиз «Подбор за 30 секунд»',
    function(){ showSuccess('✅ Расчёт в пути!', 'Менеджер соберёт расчёт и пришлёт контакты дилера для установки. Обычно — в течение рабочего дня.'); },
    function(msg){ showLeadError(btn, msg); });
  });
}

function openQuiz(mode){
  quizState = {step:0, answers:{}, mode:mode || 'modal'};
  if(mode === 'inline'){
    var box = document.getElementById('zs-quiz-inline');
    if(!box){
      box = document.createElement('div');
      box.id = 'zs-quiz-inline';
      box.style.cssText = 'max-width:640px;margin:0 auto;padding:24px;background:#fff;border:1px solid ' + LINE + ';border-radius:16px;box-shadow:0 10px 30px rgba(15,23,42,.06)';
      var mainEl = document.querySelector('main');
      if(mainEl && mainEl.parentNode) mainEl.parentNode.insertBefore(box, mainEl); else document.body.appendChild(box);
    }
    renderQuiz(box);
    var old = document.querySelector('.quiz-wrap');
    if(old) old.style.display = 'none';
    box.scrollIntoView({behavior:'smooth', block:'start'});
    return;
  }
  openPanel('<div style="display:flex;justify-content:flex-end;margin:-8px -8px 0 0"><button type="button" data-zs-close style="border:none;background:#F1F5F9;border-radius:50%;width:36px;height:36px;font-size:18px;cursor:pointer">✕</button></div><div id="zs-quiz-body"></div>');
  panel.querySelector('[data-zs-close]').addEventListener('click', closeAll);
  renderQuiz(panel.querySelector('#zs-quiz-body'));
}

/* ---------- Перехват кликов ---------- */
document.addEventListener('click', function(e){
  var add = e.target.closest('.sku-add, .pc-add');
  if(add){
    e.preventDefault(); e.stopPropagation();
    var box = add.closest('[data-price]') || add.closest('.card-product') || add.closest('div');
    var price = '', name = '';
    var priceEl = box && (box.getAttribute('data-price') || '');
    if(priceEl) price = parseInt(priceEl, 10).toLocaleString('ru-RU') + ' ₽';
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
    openQuiz('modal');
    return;
  }
  if(e.target.closest('[data-zs-close]')){ closeAll(); }
}, true);

/* На /quiz/ рендерим квиз встроенно */
if(location.pathname === '/quiz/' || location.pathname === '/quiz/index.html'){
  if(document.readyState !== 'loading') openQuiz('inline');
  else document.addEventListener('DOMContentLoaded', function(){ openQuiz('inline'); });
}
/* P0-3: экспорт модалки, подсказки городов, мягкая маска телефона */
window.ZS_OPEN_LEAD = openLead;
var ZS_CITIES = ['Москва','Санкт-Петербург','Екатеринбург','Новосибирск','Казань','Нижний Новгород','Красноярск','Самара','Тюмень','Уфа','Челябинск','Пермь','Ростов-на-Дону','Воронеж','Краснодар','Волгоград','Саратов','Иркутск','Хабаровск','Владивосток','Калининград','Тольятти','Омск','Барнаул','Ульяновск'];
function zsEnsureCities(){
  if(document.getElementById('zs-cities')) return;
  var dl = document.createElement('datalist'); dl.id = 'zs-cities';
  ZS_CITIES.forEach(function(c){ var o = document.createElement('option'); o.value = c; dl.appendChild(o); });
  document.body.appendChild(dl);
  document.querySelectorAll('input[name=city]').forEach(function(el){ el.setAttribute('list','zs-cities'); });
}
function zsFmtPhone(el){
  var v = el.value || '';
  if(!/^[\d\+\(\)\-\s]*$/.test(v)) return;
  var d = v.replace(/\D/g,'');
  if(!d) return;
  if(d[0] === '8') d = '7' + d.slice(1);
  if(d[0] !== '7') d = '7' + d;
  var s = '+7 (' + d.slice(1,4);
  if(d.length >= 4) s += ') ' + d.slice(4,7);
  if(d.length >= 7) s += '-' + d.slice(7,9);
  if(d.length >= 9) s += '-' + d.slice(9,11);
  el.value = s;
}
document.addEventListener('input', function(e){
  var el = e.target;
  if(el && (el.name === 'contact' || el.name === 'phone') && el.getAttribute && el.getAttribute('type') === 'tel'){ zsFmtPhone(el); }
}, true);
if(document.readyState !== 'loading'){ zsEnsureCities(); }
else { document.addEventListener('DOMContentLoaded', zsEnsureCities); }
})();
