(function(){
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
  if(tabs.length){
    var views = tabs.map(function(t){ return t.getAttribute('data-view'); });
    function show(view){
      if(views.indexOf(view) < 0) view = views[0];
      tabs.forEach(function(t){
        var on = t.getAttribute('data-view') === view;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
      });
    }
    tabs.forEach(function(t){
      t.addEventListener('click', function(){
        var v = t.getAttribute('data-view'); show(v);
        try{ history.replaceState(null, '', v === views[0] ? location.pathname : '#' + v); }catch(e){ location.hash = v; }
      });
    });
    show((location.hash || '').slice(1));
    window.addEventListener('hashchange', function(){ show(location.hash.slice(1)); });
  }
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.term').forEach(function(b){
    b.addEventListener('click', function(){
      var n = document.getElementById(b.getAttribute('data-note'));
      if(!n) return;
      n.scrollIntoView({behavior: reduce ? 'auto' : 'smooth', block: 'nearest'});
      n.classList.remove('flash'); void n.offsetWidth; n.classList.add('flash');
      setTimeout(function(){ n.classList.remove('flash'); }, 1600);
    });
  });
})();

/* ---- 在注解页每一节下面显示原文段落 ---- */
(function(){
  var main = document.querySelector('main[data-para]');
  if(!main || !window.fetch) return;
  var bar = document.getElementById('orig-bar');
  function b64(s){ var bin = atob(s), u = new Uint8Array(bin.length); for(var i=0;i<bin.length;i++) u[i]=bin.charCodeAt(i); return u; }
  function hex(h){ var u = new Uint8Array(h.length/2); for(var i=0;i<u.length;i++) u[i]=parseInt(h.substr(i*2,2),16); return u; }
  function esc(t){ var d=document.createElement('div'); d.textContent=t; return d.innerHTML; }
  function render(data){
    document.querySelectorAll('.orig').forEach(function(box){
      var i = +box.getAttribute('data-sec'), sec = data.sections[i];
      if(sec === undefined) return;
      if(sec === null){ box.innerHTML = '<p class="orig-none">本节的原文和上一节在同一段落里，见上一节。</p>'; return; }
      var html = sec.map(function(p){ return '<p>'+esc(p)+'</p>'; }).join('');
      var short = sec.join('').length < 2500;
      var col = box.parentNode, summ = col.querySelector('.summary'), quote = col.querySelector('.quote');
      var label = document.createElement('div');
      label.className = 'sum-label';
      if(short){
        // 短的节：原文在上、展开；提要在下，作为读完后的复核
        box.innerHTML = '<details open><summary>原文 · '+sec.length+' 段</summary><div class="orig-text">'+html+'</div></details>';
        col.insertBefore(box, quote || summ);
        if(quote) quote.hidden = true;
        label.textContent = '提要';
      }else{
        // 长的节：提要在上作导读，原文折叠在下
        box.innerHTML = '<details><summary>原文 · '+sec.length+' 段（较长，点开阅读）</summary><div class="orig-text">'+html+'</div></details>';
        label.textContent = '提要 · 导读';
      }
      if(summ && !col.querySelector('.sum-label')) col.insertBefore(label, summ);
    });
    if(bar) bar.hidden = true;
  }
  async function decryptWith(key, rec){
    var pt = await crypto.subtle.decrypt({name:'AES-GCM', iv:b64(rec.iv)}, key, b64(rec.ct));
    return JSON.parse(new TextDecoder().decode(pt));
  }
  async function derive(pw, rec){
    var base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey({name:'PBKDF2', salt:hex(rec.salt), iterations:rec.iter, hash:'SHA-256'}, base,
      {name:'AES-GCM', length:256}, true, ['decrypt']);
  }
  var storeKey = function(rec){ return 'mx_key_' + rec.salt; };
  fetch(main.getAttribute('data-para'), {cache:'no-cache'}).then(function(r){ return r.json(); }).then(async function(rec){
    if(rec.sections){ render(rec); return; }
    if(!window.crypto || !crypto.subtle) return;
    var saved = null;
    try{ saved = localStorage.getItem(storeKey(rec)); }catch(e){}
    if(saved){
      try{
        var k = await crypto.subtle.importKey('raw', b64(saved), {name:'AES-GCM'}, false, ['decrypt']);
        render(await decryptWith(k, rec)); return;
      }catch(e){ try{ localStorage.removeItem(storeKey(rec)); }catch(_){} }
    }
    if(!bar) return;
    bar.hidden = false;
    bar.addEventListener('submit', async function(ev){
      ev.preventDefault();
      var err = document.getElementById('orig-err'); err.hidden = true;
      var btn = bar.querySelector('button'); btn.disabled = true; btn.textContent = '正在解密…';
      try{
        var key = await derive(document.getElementById('orig-pw').value, rec);
        var data = await decryptWith(key, rec);
        if(document.getElementById('orig-rem').checked){
          var raw = new Uint8Array(await crypto.subtle.exportKey('raw', key));
          var s = ''; raw.forEach(function(c){ s += String.fromCharCode(c); });
          try{ localStorage.setItem(storeKey(rec), btoa(s)); }catch(e){}
        }
        render(data);
      }catch(e){ err.hidden = false; }
      btn.disabled = false; btn.textContent = '显示原文';
    });
  }).catch(function(){});
})();
