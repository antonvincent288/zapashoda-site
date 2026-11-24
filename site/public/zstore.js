/* zstore.js — глобальный кокпит zapashoda-ev: единое состояние машины для всех страниц.
   Итерация 1 ТЗ. Vanilla, без фреймворков (сайт на Astro). Хранение: localStorage zh_cockpit_v1. */
(function () {
  var KEY = 'zh_cockpit_v1';
  var DEF = {
    carId: 'zeekr-001-001-fr',
    carName: 'Zeekr 001 · 100 кВт·ч',
    portTag: 'GB/T DC · 200 кВт',
    baseKm: 540,
    soc: 80,
    temp: -20,
    city: 'Москва',
    roundTrip: false,
    scenMult: 1,
    ts: 0
  };
  var CHART_TEMPS = [-20, -10, 0, 10, 20, 30];
  var CHART_PCTS = [45, 70, 84, 97, 100, 90];
  var s = {};
  try { s = Object.assign({}, DEF, JSON.parse(localStorage.getItem(KEY) || '{}')); } catch (e) { s = Object.assign({}, DEF); }
  var subs = [];
  var lastW = 0, pend = null;
  function read(){ try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e){ return {}; } }
  function persist(){ try { localStorage.setItem(KEY, JSON.stringify(s)); } catch(e){} }
  function nearest(t){ var idx=4, best=1e9; for (var i=0;i<CHART_TEMPS.length;i++){ var d=Math.abs(CHART_TEMPS[i]-t); if (d<best){best=d;idx=i;} } return idx; }
  var ZS = {
    get: function(){ return s; },
    set: function(p){
      var w = 0; for (var k in p) w++;
      Object.assign(s, p || {}); s.ts = Date.now();
      var now = Date.now();
      var fire = function(){
        for (var i=0;i<subs.length;i++){ try { subs[i](s); } catch(e){} }
        window.dispatchEvent(new CustomEvent('zs:change', { detail: s }));
      };
      if (now - lastW > 500) { lastW = now; persist(); fire(); if (pend){ clearTimeout(pend); pend = null; } }
      else { if (pend) clearTimeout(pend); pend = setTimeout(function(){ pend = null; persist(); fire(); }, 500); }
    },
    subscribe: function(f){ subs.push(f); try { f(s); } catch(e){} return function(){ var i = subs.indexOf(f); if (i>=0) subs.splice(i,1); }; },
    tempPct: function(){ return CHART_PCTS[nearest(s.temp || -20)] / 100; },
    range: function(){ return Math.round((s.baseKm || 540) * ((s.soc || 80) / 100) * ZS.tempPct() * (s.scenMult || 1) * (s.roundTrip ? 0.5 : 1)); },
    tempIdx: nearest
  };
  window.addEventListener('storage', function(e){ if (e.key === KEY && e.newValue) { try { var fresh = JSON.parse(e.newValue); var w=0; for (var k in fresh) w++; Object.assign(s, fresh); for (var j=0;j<subs.length;j++){ try { subs[j](s); } catch(e2){} } window.dispatchEvent(new CustomEvent('zs:change', { detail: s })); } catch(e3){} } });
  window.ZS = ZS;
})();

/* ---- ZH HOME KIT v1 (24.11.2026): подключение унификации плиток/эффектов + фикс overflow-x + баннер «сайт наполняется».
   Файл /zh_home_kit.js, показывает баннер 1 раз в 7 дней (localStorage zh_wip_dismiss), ничего не ломает на проде. ---- */
(function () {
  try {
    var s = document.createElement('script');
    s.src = '/zh_home_kit.js?v=1';
    s.defer = true;
    document.head.appendChild(s);
  } catch (e) {}
})();
