/*! zh_home_kit.js v8 — геометрия главной (сдвиг 448 без пустоты справа), унификация плиток, модалка «СКОРО БУДЕТ КРУТО!»
 * Стиль = наш HMI-виджет. Не меняет прод-разметку: только собственные элементы zh-wip-*. */
(function(){
  try{
    if(window.__zhHomeKit)return; window.__zhHomeKit=1;
    var EASE='cubic-bezier(.22,1,.36,1)';
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
      'html:not(#zh) table{border-collapse:collapse!important}',
      '.bgrid{align-items:stretch!important}.bgrid .card{display:flex;flex-direction:column;justify-content:space-between;height:100%!important;gap:10px}',
      '.kbgrid{align-items:stretch!important}.kbcard{display:flex;flex-direction:column;justify-content:space-between;height:100%!important;gap:8px}',
      '.hw-routes{align-items:stretch!important}.hw-route{min-height:58px}',
      '.bdg{background:rgba(255,255,255,.06)!important;color:#AEB6C4!important;border:1px solid rgba(255,255,255,.13)!important}',
      '.bdg.cool{background:rgba(255,111,0,.15)!important;color:#FF8F33!important;border:1px solid rgba(255,111,0,.5)!important}',
      '.ktag{font-size:12.5px!important;letter-spacing:.04em!important;color:#9AA3B2!important}',
      '.hw-rt span{font-size:12.5px!important;color:#9AA3B2!important}',
      '.m-faq details{padding:16px 0!important}.m-faq summary{min-height:48px!important;cursor:pointer}',
      '.hw-btn{padding:15px 30px!important;border-radius:12px!important;letter-spacing:.01em!important;display:inline-flex;align-items:center;gap:8px}',
      '@media(max-width:760px){.zh-nav-col{border-top:1px solid rgba(255,255,255,.09);padding-top:20px;margin-top:8px}.zh-nav-cols p{line-height:1.55}.m-faq summary{font-size:15.5px;line-height:1.45}}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      'main .sec .sec,main h2.sec{padding-left:0!important;margin-left:0!important}',
      '@media(min-width:821px){body.zh-ovl-on main .sec,html.zh-o-on main .sec{padding-left:448px!important;margin-left:0!important}body.zh-ovl-on main .sec .wrap,html.zh-o-on main .sec .wrap{margin-left:0!important;padding-left:0!important}body.zh-ovl-on main h2.sec,html.zh-o-on main h2.sec{padding-left:0!important;margin-left:0!important}body.zh-ovl-on main>.wrap,body.zh-ovl-on main>.hw-hero>.wrap,html.zh-o-on main>.wrap,html.zh-o-on main>.hw-hero>.wrap{margin-left:448px!important;margin-right:16px!important;max-width:none!important}body.zh-ovl-on main .sec-blk,html.zh-o-on main .sec-blk{padding-left:448px!important}body.zh-ovl-on footer,html.zh-o-on footer{padding-left:448px!important}}',
      '.hw-split{align-items:stretch!important}.hw-routes{display:flex!important;flex-direction:column!important;justify-content:space-between!important;height:100%}',
      '.hw-routes .hw-route{flex:1 1 auto!important;min-height:58px;align-items:center;gap:12px}',
      '.hw-preset,.hw-chip,.fchip,.hw-btn{border-radius:12px!important}',
      '.hw-routes .hw-rt span{font-size:12.5px!important;color:#9AA3B2!important}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      '.sec .sn,.sec .accent{white-space:nowrap;overflow:visible}',
      '.sec .accent{display:inline-block;max-width:100%;overflow-wrap:break-word!important}',
      '.cards .card:hover,.bgrid .bcard:hover,.kbgrid .kbcard:hover{border-color:rgba(255,111,0,.55)!important;box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 44px rgba(255,111,0,.16)!important;transform:translateY(-2px)!important}',
      '.cards .card,.bgrid .bcard,.kbgrid .kbcard{border-radius:12px!important;border:1px solid rgba(255,255,255,.10)!important}',
      '.bgrid{align-items:stretch!important}.bgrid .bcard{display:flex;flex-direction:column;justify-content:space-between;height:100%}',
      '.kbgrid{align-items:stretch!important}.kbgrid .kbcard{display:flex;flex-direction:column;justify-content:space-between;height:100%}',
      '.bdg{font-size:11.5px!important;letter-spacing:.08em!important;padding:4px 9px!important;border-radius:6px!important;text-transform:uppercase!important}',
      '.btn,.fchip,.preset-btn{border-radius:10px!important}',
      '.ktag,.mspec{font-size:12px!important;letter-spacing:.06em!important}',
      'html:not(#zh) table{border-collapse:collapse!important}',
      '.bgrid{align-items:stretch!important}.bgrid .card{display:flex;flex-direction:column;justify-content:space-between;height:100%!important;gap:10px}',
      '.kbgrid{align-items:stretch!important}.kbcard{display:flex;flex-direction:column;justify-content:space-between;height:100%!important;gap:8px}',
      '.hw-routes{align-items:stretch!important}.hw-route{min-height:58px}',
      '.bdg{background:rgba(255,255,255,.06)!important;color:#AEB6C4!important;border:1px solid rgba(255,255,255,.13)!important}',
      '.bdg.cool{background:rgba(255,111,0,.15)!important;color:#FF8F33!important;border:1px solid rgba(255,111,0,.5)!important}',
      '.ktag{font-size:12.5px!important;letter-spacing:.04em!important;color:#9AA3B2!important}',
      '.hw-rt span{font-size:12.5px!important;color:#9AA3B2!important}',
      '.m-faq details{padding:16px 0!important}.m-faq summary{min-height:48px!important;cursor:pointer}',
      '.hw-btn{padding:15px 30px!important;border-radius:12px!important;letter-spacing:.01em!important;display:inline-flex;align-items:center;gap:8px}',
      '@media(max-width:760px){.zh-nav-col{border-top:1px solid rgba(255,255,255,.09);padding-top:20px;margin-top:8px}.zh-nav-cols p{line-height:1.55}.m-faq summary{font-size:15.5px;line-height:1.45}}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      'html.zh-o-on main .sec,body.zh-ovl-on main .sec{padding-left:0!important}',
      'html.zh-o-on .sec-blk,body.zh-ovl-on .sec-blk{padding-left:0!important}',
      'html.zh-o-on footer,body.zh-ovl-on footer{padding-left:0!important}',
      'html.zh-o-on main>.wrap,html.zh-o-on main>.hw-hero>.wrap,body.zh-ovl-on main>.wrap,body.zh-ovl-on main>.hw-hero>.wrap{margin-left:auto!important;max-width:1152px!important}',
      '@media(min-width:821px){body.zh-ovl-on:has(.zhw .hud-left.open) main .sec{padding-left:448px!important}body.zh-ovl-on:has(.zhw .hud-left.open) main>.wrap,body.zh-ovl-on:has(.zhw .hud-left.open) main>.hw-hero>.wrap{margin-left:448px!important;max-width:min(1152px,calc(100vw - 488px))!important}body.zh-ovl-on:has(.zhw .hud-left.open) .sec-blk{padding-left:448px!important}body.zh-ovl-on:has(.zhw .hud-left.open) footer{padding-left:448px!important}}',
      '.hw-split{align-items:stretch!important}.hw-routes{display:flex!important;flex-direction:column!important;justify-content:space-between!important;height:100%}',
      '.hw-routes .hw-route{flex:1 1 auto!important;min-height:58px;align-items:center;gap:12px}',
      '.hw-preset,.hw-chip,.fchip,.hw-btn{border-radius:12px!important}',
      '.hw-routes .hw-rt span{font-size:12.5px!important;color:#9AA3B2!important}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      '.sec .sn,.sec .accent{white-space:nowrap;overflow:visible}',
      '.sec .accent{display:inline-block;max-width:100%;overflow-wrap:break-word!important}',
      '.cards .card:hover,.bgrid .bcard:hover,.kbgrid .kbcard:hover{border-color:rgba(255,111,0,.55)!important;box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 44px rgba(255,111,0,.16)!important;transform:translateY(-2px)!important}',
      '.cards .card,.bgrid .bcard,.kbgrid .kbcard{border-radius:12px!important;border:1px solid rgba(255,255,255,.10)!important}',
      '.bgrid{align-items:stretch!important}.bgrid .bcard{display:flex;flex-direction:column;justify-content:space-between;height:100%}',
      '.kbgrid{align-items:stretch!important}.kbgrid .kbcard{display:flex;flex-direction:column;justify-content:space-between;height:100%}',
      '.bdg{font-size:11.5px!important;letter-spacing:.08em!important;padding:4px 9px!important;border-radius:6px!important;text-transform:uppercase!important}',
      '.btn,.fchip,.preset-btn{border-radius:10px!important}',
      '.ktag,.mspec{font-size:12px!important;letter-spacing:.06em!important}',
      'html:not(#zh) table{border-collapse:collapse!important}',
      '.bgrid{align-items:stretch!important}.bgrid .card{display:flex;flex-direction:column;justify-content:space-between;height:100%!important;gap:10px}',
      '.kbgrid{align-items:stretch!important}.kbcard{display:flex;flex-direction:column;justify-content:space-between;height:100%!important;gap:8px}',
      '.hw-routes{align-items:stretch!important}.hw-route{min-height:58px}',
      '.bdg{background:rgba(255,255,255,.06)!important;color:#AEB6C4!important;border:1px solid rgba(255,255,255,.13)!important}',
      '.bdg.cool{background:rgba(255,111,0,.15)!important;color:#FF8F33!important;border:1px solid rgba(255,111,0,.5)!important}',
      '.ktag{font-size:12.5px!important;letter-spacing:.04em!important;color:#9AA3B2!important}',
      '.hw-rt span{font-size:12.5px!important;color:#9AA3B2!important}',
      '.m-faq details{padding:16px 0!important}.m-faq summary{min-height:48px!important;cursor:pointer}',
      '.hw-btn{padding:15px 30px!important;border-radius:12px!important;letter-spacing:.01em!important;display:inline-flex;align-items:center;gap:8px}',
      '@media(max-width:760px){.zh-nav-col{border-top:1px solid rgba(255,255,255,.09);padding-top:20px;margin-top:8px}.zh-nav-cols p{line-height:1.55}.m-faq summary{font-size:15.5px;line-height:1.45}}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      'main .sec .sec,main h2.sec{padding-left:0!important;margin-left:0!important}',
      '@media(min-width:821px){body.zh-ovl-on main .sec,html.zh-o-on main .sec{padding-left:448px!important;margin-left:0!important}body.zh-ovl-on main .sec .wrap,html.zh-o-on main .sec .wrap{margin-left:0!important;padding-left:0!important}body.zh-ovl-on main h2.sec,html.zh-o-on main h2.sec{padding-left:0!important;margin-left:0!important}body.zh-ovl-on main>.wrap,body.zh-ovl-on main>.hw-hero>.wrap,html.zh-o-on main>.wrap,html.zh-o-on main>.hw-hero>.wrap{margin-left:448px!important;margin-right:16px!important;max-width:none!important}body.zh-ovl-on main .sec-blk,html.zh-o-on main .sec-blk{padding-left:448px!important}body.zh-ovl-on footer,html.zh-o-on footer{padding-left:448px!important}}',
      '.hw-split{align-items:stretch!important}.hw-routes{display:flex!important;flex-direction:column!important;justify-content:space-between!important;height:100%}',
      '.hw-routes .hw-route{flex:1 1 auto!important;min-height:58px;align-items:center;gap:12px}',
      '.hw-preset,.hw-chip,.fchip,.hw-btn{border-radius:12px!important}',
      '.hw-routes .hw-rt span{font-size:12.5px!important;color:#9AA3B2!important}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      '.sec .sn,.sec .accent{white-space:nowrap;overflow:visible}',
      '.sec .accent{display:inline-block;max-width:100%;overflow-wrap:break-word!important}',
      '.cards .card:hover,.bgrid .bcard:hover,.kbgrid .kbcard:hover{border-color:rgba(255,111,0,.55)!important;box-shadow:0 18px 50px rgba(0,0,0,.45),0 0 44px rgba(255,111,0,.16)!important;transform:translateY(-2px)!important}',
      '.cards .card,.bgrid .bcard,.kbgrid .kbcard{border-radius:12px!important;border:1px solid rgba(255,255,255,.10)!important}',
      '.bgrid{align-items:stretch!important}.bgrid .bcard{display:flex;flex-direction:column;justify-content:space-between;height:100%}',
      '.kbgrid{align-items:stretch!important}.kbgrid .kbcard{display:flex;flex-direction:column;justify-content:space-between;height:100%}',
      '.bdg{font-size:11.5px!important;letter-spacing:.08em!important;padding:4px 9px!important;border-radius:6px!important;text-transform:uppercase!important}',
      '.btn,.fchip,.preset-btn{border-radius:10px!important}',
      '.ktag,.mspec{font-size:12px!important;letter-spacing:.06em!important}',
      'html:not(#zh) table{border-collapse:collapse!important}',
      '.bgrid{align-items:stretch!important}.bgrid .card{display:flex;flex-direction:column;justify-content:space-between;height:100%!important;gap:10px}',
      '.kbgrid{align-items:stretch!important}.kbcard{display:flex;flex-direction:column;justify-content:space-between;height:100%!important;gap:8px}',
      '.hw-routes{align-items:stretch!important}.hw-route{min-height:58px}',
      '.bdg{background:rgba(255,255,255,.06)!important;color:#AEB6C4!important;border:1px solid rgba(255,255,255,.13)!important}',
      '.bdg.cool{background:rgba(255,111,0,.15)!important;color:#FF8F33!important;border:1px solid rgba(255,111,0,.5)!important}',
      '.ktag{font-size:12.5px!important;letter-spacing:.04em!important;color:#9AA3B2!important}',
      '.hw-rt span{font-size:12.5px!important;color:#9AA3B2!important}',
      '.m-faq details{padding:16px 0!important}.m-faq summary{min-height:48px!important;cursor:pointer}',
      '.hw-btn{padding:15px 30px!important;border-radius:12px!important;letter-spacing:.01em!important;display:inline-flex;align-items:center;gap:8px}',
      '@media(max-width:760px){.zh-nav-col{border-top:1px solid rgba(255,255,255,.09);padding-top:20px;margin-top:8px}.zh-nav-cols p{line-height:1.55}.m-faq summary{font-size:15.5px;line-height:1.45}}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      'html.zh-o-on main .sec,body.zh-ovl-on main .sec{padding-left:0!important}',
      'html.zh-o-on .sec-blk,body.zh-ovl-on .sec-blk{padding-left:0!important}',
      'html.zh-o-on footer,body.zh-ovl-on footer{padding-left:0!important}',
      'html.zh-o-on main>.wrap,html.zh-o-on main>.hw-hero>.wrap,body.zh-ovl-on main>.wrap,body.zh-ovl-on main>.hw-hero>.wrap{margin-left:auto!important;max-width:1152px!important}',
      '@media(min-width:821px){body.zh-ovl-on:has(.zhw .hud-left.open) main .sec{padding-left:448px!important}body.zh-ovl-on:has(.zhw .hud-left.open) main>.wrap,body.zh-ovl-on:has(.zhw .hud-left.open) main>.hw-hero>.wrap{margin-left:448px!important;max-width:min(1152px,calc(100vw - 488px))!important}body.zh-ovl-on:has(.zhw .hud-left.open) .sec-blk{padding-left:448px!important}body.zh-ovl-on:has(.zhw .hud-left.open) footer{padding-left:448px!important}}',
      '.hw-split{align-items:stretch!important}.hw-routes{display:flex!important;flex-direction:column!important;justify-content:space-between!important;height:100%}',
      '.hw-routes .hw-route{flex:1 1 auto!important;min-height:58px;align-items:center;gap:12px}',
      '.hw-preset,.hw-chip,.fchip,.hw-btn{border-radius:12px!important}',
      '.hw-routes .hw-rt span{font-size:12.5px!important;color:#9AA3B2!important}',
      '.sec small{white-space:normal!important;overflow:visible!important;word-break:break-word!important;max-width:100%}',
      '.sec .sn,.sec .accent{white-space:nowrap;overflow:visible}',
      'main .sec .sec,main h2.sec{padding-left:0!important;margin-left:0!important}',
      '@media(min-width:821px){body.zh-ovl-on main .sec,html.zh-o-on main .sec{padding-left:448px!important;margin-left:0!important}body.zh-ovl-on main .sec .wrap,html.zh-o-on main .sec .wrap{margin-left:0!important;padding-left:0!important}body.zh-ovl-on main h2.sec,html.zh-o-on main h2.sec{padding-left:0!important;margin-left:0!important}body.zh-ovl-on main>.wrap,body.zh-ovl-on main>.hw-hero>.wrap,html.zh-o-on main>.wrap,html.zh-o-on main>.hw-hero>.wrap{margin-left:448px!important;margin-right:16px!important;max-width:none!important}body.zh-ovl-on main .sec-blk,html.zh-o-on main .sec-blk{padding-left:448px!important}body.zh-ovl-on footer,html.zh-o-on footer{padding-left:448px!important}}'
    ,'.zh-tbl-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%;padding-bottom:6px}','.zh-tbl-hint{display:none;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#6E7686;padding:2px 0 4px;text-align:right}','@media(max-width:760px){.zh-tbl-hint{display:block}}'
    ].join('');
      var st=document.createElement('style');st.id='zh-unify-css';st.textContent=css;
      (document.head||document.documentElement).appendChild(st);
    }
    function closeModal(box,overlay){
      if(!box)return;
      try{localStorage.setItem('zh_wip_dismiss',String(Date.now()));}catch(e){}
      box.style.opacity='0';box.style.transform='translateY(10px) scale(.98)';
      if(overlay)overlay.style.opacity='0';
      setTimeout(function(){if(overlay&&overlay.parentNode)overlay.parentNode.removeChild(overlay);
        if(box&&box.parentNode)box.parentNode.removeChild(box);},380);
      document.removeEventListener('keydown',onKey,true);
    }
    function onKey(e){ if(e.key==='Escape'){ var b=document.getElementById('zh-wip-box'); var o=document.getElementById('zh-wip-overlay'); if(b)closeModal(b,o);} }
    function modal(){
      try{
        var ts=Number(localStorage.getItem('zh_wip_dismiss')||0);
        if(ts && (Date.now()-ts) < 7*24*3600*1000) return;
        var o=document.createElement('div'); o.id='zh-wip-overlay';
        o.setAttribute('style','position:fixed;inset:0;z-index:2147483000;background:radial-gradient(1100px 640px at 50% 38%,rgba(255,109,41,.10),transparent 62%),rgba(9,9,11,.74);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);display:flex;align-items:center;justify-content:center;padding:22px;opacity:0;transition:opacity .32s ease');
        var b=document.createElement('div'); b.id='zh-wip-box'; b.setAttribute('role','dialog'); b.setAttribute('aria-modal','true'); b.setAttribute('aria-label','Сайт в разработке');
        b.style.cssText='position:relative;z-index:1;width:100%;max-width:620px;max-height:calc(100dvh - 48px);overflow:auto;background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(22,19,22,.93) 34%);border:1px solid rgba(255,255,255,.09);border-radius:20px;box-shadow:0 48px 140px rgba(0,0,0,.62),0 0 90px rgba(255,109,41,.13);padding:44px 44px 34px;color:#EDF0F5;font:500 15px/1.55 Inter,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;opacity:0;transform:translateY(14px) scale(.97);transition:opacity .5s '+EASE+',transform .5s '+EASE+';text-align:center';
        b.innerHTML=
          '<style id="zh-wip-inner-css">'+
          '#zh-wip-box::before{content:"";position:absolute;left:24px;right:24px;top:0;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.75) 30%,rgba(255,255,255,.15) 60%,transparent)}'+
          '#zh-wip-box::after{content:"";position:absolute;left:24px;right:24px;bottom:0;height:1px;background:linear-gradient(90deg,transparent,rgba(255,109,41,.55) 40%,rgba(255,158,68,.28) 60%,transparent)}'+
          '.zh-wip-kicker{font-size:11px;letter-spacing:.22em;font-weight:700;color:#FF8F33;text-transform:uppercase}'+
          '.zh-wip-title{margin:14px 0 0;font-weight:700;font-size:clamp(28px,5vw,42px);line-height:1.04;letter-spacing:-.03em;background:linear-gradient(92deg,#FFD199 0%,#FF9E44 38%,#FF6D29 78%);-webkit-background-clip:text;background-clip:text;color:transparent;font-variant-numeric:tabular-nums}'+
          '.zh-wip-text{margin:16px auto 0;max-width:44ch;color:#C6CEDC;font-size:16px;line-height:1.6}'+
          '.zh-wip-cta{margin-top:26px;display:flex;gap:12px;align-items:center;justify-content:center;flex-wrap:wrap}'+
          '.zh-wip-btn{display:inline-flex;align-items:center;gap:8px;min-height:50px;padding:0 24px;border-radius:12px;font-weight:700;font-size:15px;text-decoration:none;cursor:pointer;transition:transform .2s '+EASE+',box-shadow .2s '+EASE+',border-color .2s '+EASE+'}'+
          '.zh-wip-btn-primary{background:linear-gradient(135deg,#FF9E44,#FF6D29);color:#0B1018;border:1px solid rgba(255,158,68,.6);box-shadow:0 10px 34px rgba(255,109,41,.35)}'+
          '.zh-wip-btn-primary:hover{transform:translateY(-2px);box-shadow:0 16px 44px rgba(255,109,41,.45)}'+
          '.zh-wip-btn-ghost{background:rgba(255,255,255,.05);color:#C6CEDC;border:1px solid rgba(255,255,255,.14)}'+
          '.zh-wip-btn-ghost:hover{color:#EDF0F5;border-color:rgba(255,143,51,.5)}'+
          '.zh-wip-x{position:absolute;top:14px;right:14px;width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:10px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.05);color:#C6CEDC;font-size:17px;cursor:pointer;line-height:1;transition:color .2s ease,border-color .2s ease}'+
          '.zh-wip-x:hover{color:#FF8F33;border-color:rgba(255,143,51,.5)}'+
          '.zh-wip-foot{margin-top:22px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#6E7686}'+
          '@media(max-width:640px){#zh-wip-box{padding:30px 22px 24px;border-radius:18px;max-height:calc(100dvh - 176px)} .zh-wip-cta{flex-direction:column} .zh-wip-btn{width:100%;justify-content:center}}'+
          '@media(prefers-reduced-motion:reduce){#zh-wip-box,#zh-wip-overlay{transition:none}}'+
          '</style>'+
          '<button type="button" class="zh-wip-x" id="zh-wip-close" aria-label="Закрыть">\u00d7</button>'+
          '<div class="zh-wip-kicker">\u0421\u0430\u0439\u0442 \u0437\u0430\u043f\u0430\u0441\u0445\u043e\u0434\u0430 \u00b7 \u0441\u0442\u0430\u0442\u0443\u0441: \u0432 \u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0435</div>'+
          '<h2 class="zh-wip-title">\u0421\u041a\u041e\u0420\u041e \u0411\u0423\u0414\u0415\u0422 \u041a\u0420\u0423\u0422\u041e<span style="color:#FF8F33;-webkit-text-fill-color:#FF8F33">!</span></h2>'+
          '<p class="zh-wip-text">\u0421\u0430\u0439\u0442 \u043d\u0430\u043f\u043e\u043b\u043d\u044f\u0435\u0442\u0441\u044f \u0438 \u043d\u0430\u0445\u043e\u0434\u0438\u0442\u0441\u044f \u0432 \u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0435. \u041f\u043e\u0434\u043e\u0436\u0434\u0438\u0442\u0435 \u0447\u0443\u0442\u044c-\u0447\u0443\u0442\u044c \u2014 \u0438 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0430\u0439\u0442\u0435\u0441\u044c: \u043c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u044b \u043e\u0431\u043d\u043e\u0432\u043b\u044f\u0435\u043c \u043a\u0430\u0436\u0434\u044b\u0439 \u0434\u0435\u043d\u044c.</p>'+
          '<div class="zh-wip-cta"><a class="zh-wip-btn zh-wip-btn-primary" href="/charging/" id="zh-wip-go">\u041f\u043e\u0442\u0435\u0441\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u0430\u0440\u0442\u0443 \u042d\u0417\u0421 <span aria-hidden="true">\u2192</span></a>'+
          '<button type="button" class="zh-wip-btn zh-wip-btn-ghost" id="zh-wip-later">\u041f\u043e\u043a\u0430 \u043f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u0441\u0430\u0439\u0442</button></div>'+
          '<div class="zh-wip-foot">\u0417\u0430\u043f\u0430\u0441 \u0445\u043e\u0434\u0430 \u00b7 \u043e\u0431\u043d\u043e\u0432\u043b\u044f\u0435\u043c \u0435\u0436\u0435\u0434\u043d\u0435\u0432\u043d\u043e</div>';
        o.appendChild(b);
        document.body.appendChild(o);
        requestAnimationFrame(function(){requestAnimationFrame(function(){
          o.style.opacity='1'; b.style.opacity='1'; b.style.transform='none';
        });});
        o.addEventListener('click',function(e){ if(e.target===o) closeModal(b,o); });
        document.getElementById('zh-wip-close').addEventListener('click',function(){ closeModal(b,o); });
        document.getElementById('zh-wip-later').addEventListener('click',function(){ closeModal(b,o); });
        document.getElementById('zh-wip-go').addEventListener('click',function(){ try{localStorage.setItem('zh_wip_dismiss',String(Date.now()));}catch(e2){} });
        document.addEventListener('keydown',onKey,true);
        var btn=document.getElementById('zh-wip-later');
        if(btn&&btn.focus) setTimeout(function(){try{btn.focus({preventScroll:true});}catch(e3){}},560);
      }catch(e){}
    }
    function wrapTables(){
      try{
        document.querySelectorAll('main table').forEach(function(t){
          if(t.closest('.zhw')||t.closest('.zh-tbl-wrap'))return;
          var p=t.parentElement;
          if(t.scrollWidth>p.clientWidth+2){
            var w=document.createElement('div');w.className='zh-tbl-wrap';
            t.parentNode.insertBefore(w,t);w.appendChild(t);
            var h=document.createElement('div');h.className='zh-tbl-hint';h.textContent='Свайп влево → вся таблица';
            w.insertBefore(h,t);
          }
        });
      }catch(e2){}
    }
    function boot(){ injectCss(); try{wrapTables(); setTimeout(wrapTables,800);}catch(e){} setTimeout(modal,900); }

    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
  }catch(e){}
})();
