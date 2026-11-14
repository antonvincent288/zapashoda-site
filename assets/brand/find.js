/* Zapashoda: поиск (Pagefind) + цели Метрики — Z-20261114as wave */
(function(){
 try{
  /* --- цели Метрики: делегирование кликов по CTA --- */
  function goal(name){ if(window.ym){try{ym('113935123','reachGoal',name);}catch(e){}} }
  document.addEventListener('click',function(e){
    var a=e.target.closest && e.target.closest('a[href*="t.me"],a[href*="telegram."]');
    if(a){goal('tg_click');return;}
    var b=e.target.closest && e.target.closest('a,button');
    if(!b)return;
    var t=(b.innerText||'').trim();
    if(/В заявку/i.test(t)){goal('catalog_to_request');}
    else if(/Зафиксировать цену/i.test(t)){goal('card_fix_price');}
    else if(/Рассчитать с монтажом/i.test(t)){goal('card_calc');}
  },true);
  /* --- поиск: кнопка --- */
  var btn=document.createElement('button');
  btn.id='zs-search-btn';
  btn.setAttribute('aria-label','Поиск по сайту');
  btn.innerHTML='<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9ac8ff" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><line x1="16.5" y1="16.5" x2="21" y2="21"></line></svg>';
  btn.style.cssText='position:fixed;top:76px;right:12px;z-index:180;width:44px;height:44px;border-radius:50%;background:#12161d;border:1px solid rgba(90,169,255,.45);cursor:pointer;display:none;align-items:center;justify-content:center;box-shadow:0 4px 18px rgba(0,0,0,.4)';
  document.body.appendChild(btn);
  setTimeout(function(){btn.style.display='flex';},400);
  btn.addEventListener('click',openSearch);
  goal_ok=false;
  function openSearch(){
    goal('search_open');
    var ov=document.getElementById('zs-search-modal');
    if(!ov){build();}
    else{ov.style.display='flex';document.getElementById('zs-pagefind-input').focus();}
  }
  function build(){
    var ov=document.createElement('div');ov.id='zs-search-modal';
    ov.style.cssText='position:fixed;inset:0;z-index:400;background:rgba(5,8,12,.92);display:flex;align-items:flex-start;justify-content:center;padding:20px;overflow-y:auto';
    ov.innerHTML='<div id="zs-search-box" style="width:100%;max-width:640px;background:#12161d;border:1px solid rgba(255,255,255,.14);border-radius:16px;padding:16px;margin-top:6vh">'
      +'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px"><b style="color:#fff;font-size:15px">Поиск по сайту</b><span style="flex:1"></span><button id="zs-search-x" aria-label="Закрыть поиск" style="background:none;border:none;color:#8e8e93;cursor:pointer;font-size:22px;line-height:1">×</button></div>'
      +'<div id="zs-search-body"></div></div>';
    document.body.appendChild(ov);
    ov.addEventListener('click',function(e){if(e.target===ov)closeSearch();});
    document.getElementById('zs-search-x').addEventListener('click',closeSearch);
    document.addEventListener('keydown',function(e){if(e.key==='Escape')closeSearch();});
    var s=document.createElement('script');s.src='/pagefind/pagefind-ui.js';
    s.onload=function(){
      try{
        new PagefindUI({element:'#zs-search-body',showImages:false,showSubResults:true,
          translations:{placeholder:'Поиск по гайдам и каталогу…',clear_search:'Сбросить',load_more:'Показать ещё',search_label:'Поиск',zero_results:'Ничего не найдено по «[SEARCH_TERM]»',many_results:'[COUNT] результатов по «[SEARCH_TERM]»',one_result:'[COUNT] результат по «[SEARCH_TERM]»',searching:'Ищу «[SEARCH_TERM]»…'}});
        var body=document.getElementById('zs-search-body');
        body.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a');if(a){goal('search_result_click');closeSearch();}},true);
      }catch(e){}
    };
    document.head.appendChild(s);
  }
  function closeSearch(){var ov=document.getElementById('zs-search-modal');if(ov)ov.style.display='none';}
  var st=document.createElement('style');
  st.textContent='#zs-search-body{--pagefind-ui-text:#e9eef6;--pagefind-ui-heading:#ffffff;--pagefind-ui-background:#12161d;--pagefind-ui-primary:#0161EF;--pagefind-ui-border:rgba(255,255,255,.14);--pagefind-ui-tag:#1d2330;--pagefind-ui-border-width:1px;--pagefind-ui-border-radius:10px;--pagefind-ui-image-border-radius:10px;--pagefind-ui-font:inherit}'
    +'#zs-search-body .pagefind-ui__search-input{color:#fff;background:#0d1117;border:1px solid rgba(255,255,255,.14)}'
    +'#zs-search-body .pagefind-ui__result{border-bottom-color:rgba(255,255,255,.10)}'
    +'#zs-search-body .pagefind-ui__result-excerpt mark{color:#9ac8ff;background:transparent;font-weight:700}';
  document.head.appendChild(st);
 }catch(e){}
})();
