/*! zh_home_kit.js — унификация плиток/эффектов + фикс горизонтального вылезания + баннер «сайт наполняется»
 * Добавляет: единый радиус/бордер/hover (оранжевая палитра), выравнивание карточек по высоте,
 * читаемые бейджи, overflow-x fix, ненавязчивый banner (dismiss хранится в localStorage, не чаще 1 раза в 7 дней).
 * Не меняет прод-разметку и прод-JS: только CSS-инжект с высокой специфичностью и собственные классы zh-wip-*. */
(function(){
  try{
    if(window.__zhHomeKit)return; window.__zhHomeKit=1;
    function injectCss(){
      var css=[
        'html,body{overflow-x:hidden!important}',
        '.sec .accent{display:inline-block;max-width:100%;overflow-wrap:break-word!important}',
        '.cards .card:hover,.bgrid .bcard:hover,.kbgrid .kbcard:hover{border-color:rgba(255,111,0,.55)!important;box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 44px rgba(255,111,0,.16)!important;transform:translateY(-2px)!important}',
        '.cards .card,.bgrid .bcard,.kbgrid .kbcard{border-radius:12px!important;border:1px solid rgba(255,255,255,.10)!important}',
        '.bgrid{align-items:stretch!important}.bgrid .bcard{display:flex;flex-direction:column;justify-content:space-between;height:100%}',
        '.kbgrid{align-items:stretch!important}.kbgrid .kbcard{display:flex;flex-direction:column;justify-content:space-between;height:100%}',
        '.bdg{font-size:11.5px!important;letter-spacing:.08em!important;padding:4px 9px!important;border-radius:6px!important;text-transform:uppercase!important}',
        '.btn,.fchip,.preset-btn{border-radius:10px!important}',
        '.ktag,.mspec{font-size:12px!important;letter-spacing:.06em!important}',
        'html:not(#zh) table{border-collapse:collapse!important}'
      ].join('');
      var st=document.createElement('style');st.id='zh-unify-css';st.textContent=css;
      (document.head||document.documentElement).appendChild(st);
    }
    function banner(){
      try{
        var ds=localStorage.getItem('zh_wip_dismiss');
        var ts=Number(ds||0);
        var now=Date.now();
        if(ts && (now-ts) < 7*24*3600*1000) return;
        var b=document.createElement('div'); b.id='zh-wip-banner';
        b.innerHTML='<div class="zh-wip-inner"><b>Сайт наполняется</b><span>Материалы и карточки обновляются каждый день. Нашли неточность — напишите в бот, учтём.</span><button type="button" aria-label="Закрыть">\u00d7</button></div>';
        document.body.appendChild(b);
        var s2=document.createElement('style'); s2.id='zh-wip-css';
        s2.textContent='#zh-wip-banner{position:fixed;left:50%;transform:translateX(-50%) translateY(14px);bottom:18px;z-index:2147483000;max-width:560px;width:calc(100% - 32px);background:rgba(20,17,22,.94);border:1px solid rgba(255,111,0,.4);border-radius:14px;box-shadow:0 18px 50px rgba(0,0,0,.5),0 0 44px rgba(255,111,0,.14);color:#EDF0F5;opacity:0;transition:opacity .45s ease,transform .45s ease;backdrop-filter:blur(10px)}#zh-wip-banner.zh-wip-show{opacity:1;transform:translateX(-50%)}#zh-wip-inner{display:flex;align-items:center;gap:12px;padding:14px 16px;font:500 14px/1.5 Inter,system-ui,-apple-system,sans-serif}#zh-wip-inner b{color:#FF6F00;white-space:nowrap;font-weight:700}#zh-wip-inner span{flex:1;color:#C6CEDC}#zh-wip-inner button{flex:none;width:30px;height:30px;border-radius:8px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.05);color:#C6CEDC;font-size:17px;cursor:pointer;line-height:1}#zh-wip-inner button:hover{color:#FF8F33;border-color:rgba(255,143,51,.5)}@media(max-width:640px){#zh-wip-inner{padding:12px;gap:10px}#zh-wip-inner b{font-size:13px}#zh-wip-inner span{font-size:12.5px}}';
        (document.head||document.documentElement).appendChild(s2);
        setTimeout(function(){b.classList.add('zh-wip-show');},1200);
        b.querySelector('button').addEventListener('click',function(){
          b.classList.remove('zh-wip-show');
          try{localStorage.setItem('zh_wip_dismiss',String(Date.now()));}catch(e){}
          setTimeout(function(){if(b.parentNode)b.parentNode.removeChild(b);},480);
        });
      }catch(e){}
    }
    function boot(){ injectCss(); banner(); }
    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
  }catch(e){}
})();
