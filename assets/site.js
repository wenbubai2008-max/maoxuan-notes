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
