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