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

/* ---- 原文段落 + 我的笔记 ---- */
(function(){
  var main = document.querySelector('main[data-notes]');
  if(!main || !window.fetch || !window.crypto || !crypto.subtle) return;
  var ROOT = main.getAttribute('data-root') || '';
  var REPO = main.getAttribute('data-repo');
  var NOTES = main.getAttribute('data-notes');
  var PARA = main.getAttribute('data-para');
  var ITER = 310000;
  var bar = document.getElementById('orig-bar');
  var KEY = null, SALT = null;

  function b64(s){ var bin = atob(s.replace(/\s/g,'')), u = new Uint8Array(bin.length); for(var i=0;i<bin.length;i++) u[i]=bin.charCodeAt(i); return u; }
  function tob64(u){ var s=''; new Uint8Array(u).forEach(function(c){ s+=String.fromCharCode(c); }); return btoa(s); }
  function hex(h){ var u = new Uint8Array(h.length/2); for(var i=0;i<u.length;i++) u[i]=parseInt(h.substr(i*2,2),16); return u; }
  function esc(t){ var d=document.createElement('div'); d.textContent=t; return d.innerHTML; }
  function utf8b64(s){ return btoa(unescape(encodeURIComponent(s))); }
  function b64utf8(s){ return decodeURIComponent(escape(atob(s.replace(/\s/g,'')))); }
  function ls(k, v){ try{ if(v === undefined) return localStorage.getItem(k); if(v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); }catch(e){ return null; } }

  async function derive(pw, saltHex, iter){
    var base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey({name:'PBKDF2', salt:hex(saltHex), iterations:iter, hash:'SHA-256'}, base,
      {name:'AES-GCM', length:256}, true, ['encrypt','decrypt']);
  }
  async function dec(key, rec){
    var pt = await crypto.subtle.decrypt({name:'AES-GCM', iv:b64(rec.iv)}, key, b64(rec.ct));
    return JSON.parse(new TextDecoder().decode(pt));
  }
  async function enc(key, obj){
    var iv = crypto.getRandomValues(new Uint8Array(12));
    var ct = await crypto.subtle.encrypt({name:'AES-GCM', iv:iv}, key, new TextEncoder().encode(JSON.stringify(obj)));
    return {enc:'pbkdf2-sha256/aes-256-gcm', iter:ITER, salt:SALT, iv:tob64(iv), ct:tob64(ct)};
  }
  async function loadStoredKey(){
    var saved = ls('mx_key_' + SALT);
    if(!saved) return null;
    try{ return await crypto.subtle.importKey('raw', b64(saved), {name:'AES-GCM'}, true, ['encrypt','decrypt']); }
    catch(e){ ls('mx_key_' + SALT, null); return null; }
  }
  async function remember(key){
    var raw = await crypto.subtle.exportKey('raw', key);
    ls('mx_key_' + SALT, tob64(raw));
  }
  function setKey(k){ KEY = k; document.dispatchEvent(new Event('mxkey')); }

  /* 原文段落 */
  function renderParas(data){
    document.querySelectorAll('.orig').forEach(function(box){
      var i = +box.getAttribute('data-sec'), sec = data.sections[i];
      if(sec === undefined) return;
      if(sec === null){ box.innerHTML = '<p class="orig-none">本节的原文和上一节在同一段落里，见上一节。</p>'; return; }
      var html = sec.map(function(p){ return '<p>'+esc(p)+'</p>'; }).join('');
      var short = sec.join('').length < 2500;
      var col = box.parentNode, summ = col.querySelector('.summary'), quote = col.querySelector('.quote');
      var label = document.createElement('div'); label.className = 'sum-label';
      if(short){
        box.innerHTML = '<details open><summary>原文 · '+sec.length+' 段</summary><div class="orig-text">'+html+'</div></details>';
        col.insertBefore(box, quote || summ);
        if(quote) quote.hidden = true;
        label.textContent = '提要';
      }else{
        box.innerHTML = '<details><summary>原文 · '+sec.length+' 段（较长，点开阅读）</summary><div class="orig-text">'+html+'</div></details>';
        label.textContent = '提要 · 导读';
      }
      if(summ && !col.querySelector('.sum-label')) col.insertBefore(label, summ);
    });
  }

  var paraRec = null;
  function showBar(text){
    if(!bar) return;
    if(text) bar.querySelector('label').textContent = text;
    bar.hidden = false;
  }
  async function verifyKey(key){
    if(paraRec && paraRec.ct){ renderParas(await dec(key, paraRec)); return true; }
    var r = await fetch(ROOT + 'content/notes/check.json', {cache:'no-cache'});
    if(!r.ok) return true;
    var chk = await r.json();
    var v = await dec(key, chk);
    return v && v.ok === true;
  }
  if(bar){
    bar.addEventListener('submit', async function(ev){
      ev.preventDefault();
      var err = document.getElementById('orig-err'); err.hidden = true;
      var btn = bar.querySelector('button'); btn.disabled = true; btn.textContent = '正在解密…';
      try{
        var key = await derive(document.getElementById('orig-pw').value, SALT, ITER);
        if(!(await verifyKey(key))) throw new Error('bad');
        if(document.getElementById('orig-rem').checked) await remember(key);
        bar.hidden = true;
        setKey(key);
      }catch(e){ err.hidden = false; }
      btn.disabled = false; btn.textContent = '确定';
    });
  }

  async function init(){
    try{ SALT = (await (await fetch(ROOT + 'text/para/salt.txt', {cache:'no-cache'})).text()).trim(); }catch(e){ return; }
    if(PARA){
      try{ paraRec = await (await fetch(PARA, {cache:'no-cache'})).json(); }catch(e){ paraRec = null; }
      if(paraRec && paraRec.sections) renderParas(paraRec);
    }
    var k = await loadStoredKey();
    if(k){
      try{ if(paraRec && paraRec.ct) renderParas(await dec(k, paraRec)); setKey(k); return; }
      catch(e){ ls('mx_key_' + SALT, null); }
    }
    if(paraRec && paraRec.ct) showBar('输入密码，在每一节下面显示原文，并可以写自己的笔记');
    var nb = document.getElementById('mx-notes-btn');
    if(nb) nb.addEventListener('click', function(e){ e.preventDefault(); showBar('输入密码，读写自己的笔记'); document.getElementById('orig-pw').focus(); });
  }

  /* 我的笔记 */
  var TOKEN_KEY = 'mx_gh_token';
  var dlg = document.getElementById('mx-token');
  function token(){ return ls(TOKEN_KEY); }
  function openTokenDialog(){ if(dlg && dlg.showModal){ document.getElementById('mx-token-in').value = token() || ''; dlg.showModal(); } }
  document.querySelectorAll('[data-open-token]').forEach(function(a){ a.addEventListener('click', function(e){ e.preventDefault(); openTokenDialog(); }); });
  if(dlg){
    document.getElementById('mx-token-save').addEventListener('click', function(){ var v = document.getElementById('mx-token-in').value.trim(); ls(TOKEN_KEY, v || null); dlg.close(); updateStatusAll(); });
    document.getElementById('mx-token-clear').addEventListener('click', function(){ ls(TOKEN_KEY, null); document.getElementById('mx-token-in').value=''; dlg.close(); updateStatusAll(); });
    document.getElementById('mx-token-cancel').addEventListener('click', function(){ dlg.close(); });
  }

  var notes = {sections:{}}, sha = null;
  async function apiGet(){
    var r = await fetch('https://api.github.com/repos/' + REPO + '/contents/' + NOTES + '?ref=main&t=' + Date.now(),
      {headers:{'Authorization':'Bearer ' + token(), 'Accept':'application/vnd.github+json'}, cache:'no-store'});
    if(r.status === 404) return {sha:null, rec:null};
    if(!r.ok) throw new Error('get ' + r.status);
    var j = await r.json();
    return {sha:j.sha, rec:JSON.parse(b64utf8(j.content))};
  }
  async function fetchNotes(){
    if(token()){
      try{ var g = await apiGet(); sha = g.sha; return g.rec ? await dec(KEY, g.rec) : {sections:{}}; }catch(e){}
    }
    try{
      var r = await fetch(ROOT + NOTES, {cache:'no-cache'});
      if(!r.ok) return {sections:{}};
      return await dec(KEY, await r.json());
    }catch(e){ return {sections:{}}; }
  }
  function fmt(iso){ if(!iso) return ''; var d = new Date(iso); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')+' '+String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0'); }
  function draftKey(i){ return 'mx_draft_' + NOTES + '_' + i; }
  function updateStatusAll(){
    document.querySelectorAll('.mynote').forEach(function(li){ setStatus(li, li._state || ''); });
  }
  function setStatus(li, state, extra){
    li._state = state;
    var st = li.querySelector('.st');
    var saved = notes.sections[li._i];
    var msg = {'saving':'正在保存到 GitHub…','dirty':'有改动，尚未保存','error':'保存失败：' + (extra||''),'':''}[state] || '';
    if(!msg) msg = saved ? '已保存 · ' + fmt(saved.updated) : '还没有笔记';
    if(!token() && state !== 'saving') msg += ' · <a href="#" data-open-token>设置 GitHub 令牌后才能保存</a>';
    st.innerHTML = msg;
    st.querySelectorAll('[data-open-token]').forEach(function(a){ a.addEventListener('click', function(e){ e.preventDefault(); openTokenDialog(); }); });
  }
  async function save(li){
    if(!token()){ openTokenDialog(); return; }
    var i = li._i, text = li.querySelector('textarea').value;
    setStatus(li, 'saving');
    for(var attempt = 0; attempt < 2; attempt++){
      try{
        var g = await apiGet();
        var cur = g.rec ? await dec(KEY, g.rec) : {sections:{}};
        if(text.trim()) cur.sections[i] = {text:text, updated:new Date().toISOString()};
        else delete cur.sections[i];
        var body = {message:'笔记：' + NOTES.replace('content/notes/','').replace('.json','') + ' §' + (+i + 1),
                    content: utf8b64(JSON.stringify(await enc(KEY, cur)))};
        if(g.sha) body.sha = g.sha;
        var r = await fetch('https://api.github.com/repos/' + REPO + '/contents/' + NOTES,
          {method:'PUT', headers:{'Authorization':'Bearer ' + token(), 'Accept':'application/vnd.github+json'}, body:JSON.stringify(body)});
        if(r.status === 409 || r.status === 422){ continue; }
        if(!r.ok){ var t = r.status === 401 || r.status === 403 ? '令牌无效或权限不够' : ('HTTP ' + r.status); throw new Error(t); }
        notes = cur; ls(draftKey(i), null); setStatus(li, '');
        return;
      }catch(e){ setStatus(li, 'error', e.message); return; }
    }
    setStatus(li, 'error', '和别处的修改冲突，请刷新页面后再保存');
  }
  document.addEventListener('mxkey', async function(){
    var nb = document.getElementById('mx-notes-btn'); if(nb) nb.hidden = true;
    notes = await fetchNotes();
    document.querySelectorAll('.sec').forEach(function(sec, i){
      var col = sec.querySelector('.notes'); if(!col || col.querySelector('.mynote')) return;
      var li = document.createElement('li'); li.className = 'mynote'; li._i = String(i);
      var saved = notes.sections[i], draft = ls(draftKey(i));
      li.innerHTML = '<div class="head"><b>我的笔记</b><span class="kind">只有你能看到</span></div>' +
        '<textarea rows="4" placeholder="写下你读这一节的想法、疑问、联想……" aria-label="第 '+(i+1)+' 节我的笔记"></textarea>' +
        '<div class="act"><button type="button">保存</button><span class="st"></span></div>';
      var ta = li.querySelector('textarea');
      ta.value = draft !== null ? draft : (saved ? saved.text : '');
      if(ta.value.length > 120) ta.rows = 8;
      col.appendChild(li);
      setStatus(li, draft !== null && (!saved || draft !== saved.text) ? 'dirty' : '');
      ta.addEventListener('input', function(){ ls(draftKey(i), ta.value); setStatus(li, 'dirty'); });
      li.querySelector('button').addEventListener('click', function(){ save(li); });
      ta.addEventListener('keydown', function(e){ if((e.metaKey || e.ctrlKey) && e.key === 's'){ e.preventDefault(); save(li); } });
    });
  });

  init();
})();
