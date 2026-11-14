if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').catch(function(){});});}
(function(){
 function anim(el){var target=parseInt(el.getAttribute('data-count'),10)||0;if(!target){return;}var st=performance.now();var from=Math.max(0,target-40);function step(ts){var k=Math.min(1,(ts-st)/900);var ease=1-Math.pow(1-k,3);el.textContent=Math.round(from+(target-from)*ease).toLocaleString('ru-RU');if(k<1)requestAnimationFrame(step);}requestAnimationFrame(step);}
 document.querySelectorAll('[data-count]').forEach(anim);
 function closeLb(){var lb=document.getElementById('zsh-lb');if(lb){lb.parentNode.removeChild(lb);}}
 document.addEventListener('click',function(ev){
   var img=ev.target.closest('img[data-lb]');if(!img)return;
   if(img.closest('.zs-off')||img.closest('#zsh-lb')||img.closest('nav'))return;
   var w=img.naturalWidth||0;if(w<420)return;
   ev.preventDefault();
   var lb=document.createElement('div');lb.id='zsh-lb';
   lb.style.cssText='position:fixed;inset:0;background:rgba(0,30,43,.92);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px;cursor:zoom-out';
   var big=document.createElement('img');big.src=img.currentSrc||img.src;
   big.style.cssText='max-width:100%;max-height:92%;border-radius:8px;box-shadow:0 10px 60px rgba(0,0,0,.4)';
   lb.appendChild(big);lb.addEventListener('click',closeLb);
   document.addEventListener('keydown',function(e){if(e.key==='Escape')closeLb();},{once:true});
   document.body.appendChild(lb);
 },true);
})();
/* ---- R-01: Динамический VIN-лендинг (SEO 2.0) ---- */
(function(){
 try{
  if(sessionStorage.getItem('zsvl'))return;
  var ref=document.referrer||'';
  if(!ref)return;
  var u=null;try{u=new URL(ref);}catch(e){return;}
  var host=(u.hostname||'').replace('www.','');
  if(!/(google|yandex|ya\.ru|bing|duckduckgo)/.test(host))return;
  var q=(u.searchParams.get('q')||u.searchParams.get('text')||'').toLowerCase();
  if(!q||q.length<6)return;
  var MODELS=[['zeekr 001','zeekr-001-001-fr'],['zeekr 007','zeekr-007'],['zeekr x','zeekr-x'],['zeekr 7x','zeekr-7x'],['li auto l7','li-auto-l7-l7-pro'],['li l7','li-auto-l7-l7-pro'],['li auto l8','li-auto-l7-l8'],['li auto l9','li-auto-l7-l9'],['voyah free','voyah-free'],['voyah dream','voyah-dream'],['byd seal','byd-seal'],['byd atto','byd-atto-3'],['avatr 11','avatr-11'],['avatr 12','avatr-12'],['deepal s07','changan-deepal-s07'],['geometry c','geely-geometry-c'],['geely ex5','geely-ex5'],['mg4','mg4'],['xpeng p7','xpeng-p7'],['hongqi e-hs9','hongqi-e-hs9'],['tesla model y','tesla-model-y'],['tesla model 3','tesla-model-3']];
  var model=null;for(var i=0;i<MODELS.length;i++){if(q.indexOf(MODELS[i][0])!==-1){model=MODELS[i];break;}}
  var PAINS=[['не заряжает','/pain/ne-zaryazhaetsya/','Электромобиль не заряжается: первые действия'],['зим|мороз|холод','/blog/zimnyaya-zaryadka-medlennee/','Зимняя зарядка: почему медленнее'],['адаптер','/pain/adapter-gbt/','Адаптер Type 2 ↔ GB/T'],['gbt','/pain/adapter-gbt/','Порты GB/T и переходники'],['простой|штраф за простой','/blog/plata-za-prostoy-na-zaryadnyh-stanciyah/','Плата за простой на станциях'],['скорость|медленн|мощность отдаёт','/blog/stanciya-otdaet-menshe-moshchnosti/','Станция отдаёт меньше заявленной мощности'],['не работает станция|станция не работает','/blog/stanciya-ne-rabotaet/','Станция не работает: алгоритм'],['застрял|состоял|батареи деград|ресурс батар','/blog/skolko-zhivet-batareya-elektromobilya/','Сколько живёт батарея EV']];
  var pain=null;for(var j=0;j<PAINS.length;j++){var rx=new RegExp(PAINS[j][0]);if(rx.test(q)){pain=PAINS[j];break;}}
  if(!model&&!pain)return;
  var main=document.querySelector('main.container');if(!main)return;
  var box=document.createElement('div');box.className='gbox';box.id='zs-vin-land';
  box.style.cssText='background:#1d1d1f;color:#f5f5f7;border-radius:14px;padding:18px 20px;margin:18px 0;border-left:4px solid #0161EF';
  var title=model?('Под вашу '+(model[0].replace(/\b\w/g,function(c){return c.toUpperCase();}))+(pain?': '+pain[2]:''))
                :('Под ваш запрос: '+pain[2]);
  var links='';
  if(model)links+='<a href="/models/'+model[1]+'" style="color:#0161EF;text-decoration:underline">Карточка модели: разъёмы и совместимость</a><br>';
  if(pain)links+='<a href="'+pain[1]+'" style="color:#0161EF;text-decoration:underline">'+pain[2]+'</a>';
  box.innerHTML='<div style="font-size:12px;letter-spacing:.08em;color:#8e8e93">ПОД ВАШ ЗАПРОС · ЗАПАС ХОДА</div>'
   +'<h3 style="color:#f5f5f7;margin:6px 0 8px;font-size:19px">'+title+'</h3>'
   +links
   +'<div style="margin-top:10px;font-size:13px;color:#c9c9cf">Цена ошибки при смене разъёма — недешёвая. Проверьте свою модель и сценарий за 2 минуты.</div>'
   +'<a href="/calculator/" style="display:inline-block;margin-top:10px;background:#0161EF;color:#fff;font-weight:700;padding:8px 14px;border-radius:8px;text-decoration:none">Проверить мой сценарий</a>';
  main.insertBefore(box,main.firstChild);
  if(window.ym){try{ym('113935123','reachGoal','vin_landing_shown');}catch(e){}}
  sessionStorage.setItem('zsvl','1');
 }catch(e){}
})();

/* ---- R-08: Нейро-ассистент «Бортовой ИИ» (проактивный совет, MVP) ---- */
(function(){
 try{
  if(sessionStorage.getItem('zsai'))return;
  var h=new Date().getHours();
  var winter=(new Date().getMonth()>=9||new Date().getMonth()<=2);
  var path=location.pathname;
  var tips=[];
  if(winter){tips.push(['При минусах полная сессия быстрой зарядки идёт в 1,5–2 раза дольше — планируйте запасные станции.','/blog/zimnyaya-zaryadka-medlennee/']);}
  if(path.indexOf('/calculator')!==-1){tips.push(['Считаете бюджет? Проверьте ещё «цену простоя» — сколько стоит застрять без заряда.','#dt-calc']);}
  if(path.indexOf('/pain')!==-1||path.indexOf('/blog')!==-1){tips.push(['Хотите разбор под вашу модель? Карточки моделей: разъёмы, адаптеры, совместимость.','/catalog/']);}
  if(!tips.length){tips.push(['Не знаешь, что заряжать и сколько это стоит? Посчитай свой сценарий за минуту.','/calculator/']);}
  var t=tips[0];
  var toast=document.createElement('div');toast.id='zs-ai-toast';
  var compact=window.innerWidth<1024?'84px':'16px';
  toast.style.cssText='position:fixed;left:50%;transform:translateX(-50%) translateY(8px);width:min(560px,calc(100vw - 24px));bottom:'+compact+';z-index:190;background:rgba(18,22,28,.92);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);color:#f5f5f7;border:1px solid rgba(90,169,255,.35);border-radius:12px;padding:9px 12px;font-size:12.5px;line-height:1.35;box-shadow:0 8px 40px rgba(0,0,0,.45),0 0 24px rgba(90,169,255,.10);display:flex;align-items:center;gap:10px;opacity:0;transition:opacity .45s ease,transform .45s ease';
  toast.innerHTML='<span id="zs-ai-tag" style="flex:none;font:700 10px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.12em;color:#00E5FF;border:1px solid rgba(0,229,255,.4);border-radius:6px;padding:4px 7px;background:rgba(0,229,255,.08);white-space:nowrap">AI</span><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+t[0]+'</span><a href="'+t[1]+'" id="zs-ai-go" style="flex:none;display:flex;align-items:center;gap:6px;color:#5AA9FF;font-weight:700;font-size:12.5px;text-decoration:none;white-space:nowrap;padding:6px 10px;border-radius:8px;border:1px solid rgba(90,169,255,.35);background:rgba(90,169,255,.10)">Открыть<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#5AA9FF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a><button id="zs-ai-x" style="flex:none;background:none;border:none;color:#8e8e93;cursor:pointer;font-size:16px;line-height:1;padding:8px 6px;min-height:24px;min-width:24px" aria-label="Скрыть">×</button>';
  setTimeout(function(){
    document.body.appendChild(toast);
    requestAnimationFrame(function(){ requestAnimationFrame(function(){ toast.style.opacity='1'; toast.style.transform='translateX(-50%) translateY(0)'; }); });
    if(window.ym){try{ym('113935123','reachGoal','ai_toast_shown');}catch(e){}}
    document.getElementById('zs-ai-go').addEventListener('click',function(){if(window.ym){try{ym('113935123','reachGoal','ai_toast_click');}catch(e){}}sessionStorage.setItem('zsai','1');});
    document.getElementById('zs-ai-x').addEventListener('click',function(){toast.style.opacity='0';toast.style.transform='translateX(-50%) translateY(8px)';setTimeout(function(){toast.remove();},480);sessionStorage.setItem('zsai','1');});
    setTimeout(function(){var el=document.getElementById('zs-ai-toast');if(el){el.style.opacity='0';el.style.transform='translateX(-50%) translateY(8px)';setTimeout(function(){if(el.parentNode)el.remove();},480);}},14000);
  },4000);
 }catch(e){}
})();
