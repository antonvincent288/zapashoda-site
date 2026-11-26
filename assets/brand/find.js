/* Zapashoda: цели Метрики (поиск живёт в хедере и на /search/) — Z-20261114at wave, дубль кнопки поиска снят */
(function(){
 try{
  function goal(name){ if(window.ym){try{ym('113935123','reachGoal',name);}catch(e){}} }
  /* поиск в хедере: факты использования */
  var hf=document.querySelector('form.hsearch');
  if(hf){hf.addEventListener('submit',function(){goal('header_search_submit');});}
  /* делегированные цели по кликам */
  document.addEventListener('click',function(e){
    var a=e.target.closest && e.target.closest('a[href*="t.me"],a[href*="telegram."]');
    if(a){goal('tg_click');return;}
    var b=e.target.closest && e.target.closest('a,button');
    if(!b)return;
    if(b.classList.contains('pf-item')){goal('search_result_click');return;}
    var t=(b.innerText||'').trim();
    if(/В заявку/i.test(t)){goal('catalog_to_request');}
    else if(/Зафиксировать цену/i.test(t)){goal('card_fix_price');}
    else if(/Рассчитать с монтажом/i.test(t)){goal('card_calc');}
  },true);
 }catch(e){}
})();
