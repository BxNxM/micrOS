(function () {
  var ID = 'micrOSAuth', rf = window.fetch && window.fetch.bind(window);
  var user = 'admin', pass = '', challenged = {};
  try {
    sessionStorage.removeItem(ID);
    sessionStorage.removeItem('micros.config.auth');
  } catch (_) {}

  function rm(e) { if (e && e.parentNode) e.parentNode.removeChild(e); }
  function load() { return {user: user, pass: pass}; }
  function save(d) {
    user = d.user || 'admin';
    pass = d.pass || '';
    return load();
  }
  function clear() { pass = ''; }
  function url(i) {
    return typeof i === 'string' ? i :
      i && typeof i.href === 'string' ? i.href :
      i && typeof i.url === 'string' ? i.url : '';
  }
  function same(i) {
    try {
      var a = document.createElement('a'), u = url(i);
      if (!u) return false;
      a.href = u;
      return a.protocol === location.protocol && a.host === location.host;
    } catch (_) { return false; }
  }
  function key(i) {
    try {
      var a = document.createElement('a'), u = url(i);
      if (!u || !same(i)) return '';
      a.href = u;
      return a.pathname;
    } catch (_) { return ''; }
  }
  function hdr(d) {
    d = d || load();
    return d.pass ? {'x-micros-auth': d.pass} : {};
  }
  function ext(a, b) {
    var o = {}, k;
    a = a || {};
    for (k in a) o[k] = a[k];
    for (k in b) o[k] = b[k];
    return o;
  }
  function mh(a, b) {
    var k, o = {};
    if (window.Headers) {
      try {
        o = new Headers(a || {});
        for (k in b) o.set(k, b[k]);
        return o;
      } catch (_) {}
    }
    a = a || {};
    for (k in a) o[k] = a[k];
    for (k in b) o[k] = b[k];
    return o;
  }
  function af(u, o, d) {
    o = o || {};
    if (!rf) return Promise.reject(Error('Fetch unsupported'));
    return rf(u, ext(o, {headers: mh(o.headers || (u && u.headers), same(u) && d ? hdr(d) : {})}));
  }
  function gf(u, o) {
    o = o || {};
    var k = key(u), d = load();
    var proactive = o.micrOSAuth !== false && k && challenged[k] && d.pass;
    return af(u, o, proactive ? d : null).then(function (r) {
      if (r.status !== 401 || o.micrOSAuth === false || !same(u)) return r;
      challenged[k] = true;
      if (proactive) {
        clear();
        return prompt({target: u, request: o, message: 'Auth required', ok: function (pr) { return pr; }});
      }
      if (d.pass) {
        return af(u, o, d).then(function (rr) {
          if (rr.status !== 401) return rr;
          clear();
          return prompt({target: u, request: o, message: 'Auth required', ok: function (pr) { return pr; }});
        });
      }
      return prompt({target: u, request: o, message: 'Auth required', ok: function (rr) { return rr; }});
    });
  }
  function css() {
    if (document.getElementById(ID + 'Style')) return;
    var s = document.createElement('style');
    s.id = ID + 'Style';
    s.textContent = '#' + ID + '{position:fixed;top:0;right:0;bottom:0;left:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:#0009;font:14px sans-serif;color:#fff}#' + ID + ' form{display:flex;flex-direction:column;width:240px;max-width:90%;padding:14px;border:1px solid #555;border-radius:6px;background:#161022}#' + ID + ' input,#' + ID + ' button{display:block;width:100%;min-width:0;max-width:none;flex:none;height:32px;min-height:32px;margin:8px 0 0;border-radius:4px;border:1px solid #555;padding:0 9px;box-sizing:border-box;font:14px sans-serif}#' + ID + ' input{background:#241a36;color:#fff;font-size:16px}#' + ID + ' button{background:#17823a;color:#fff;font-weight:bold}#' + ID + ' span{min-height:18px;margin-top:6px;color:#ff9a9a}#' + ID + ' pre{white-space:pre-wrap;word-break:break-word}';
    (document.head || document.getElementsByTagName('head')[0]).appendChild(s);
  }
  function prompt(o) {
    o = o || {};
    css();
    rm(document.getElementById(ID));
    var d = load(), p = document.createElement('div'), f, e, m, t;
    p.id = ID;
    p.innerHTML = '<form><strong>micrOS Auth</strong><input name="user" autocomplete="username" placeholder="Username"><input name="pass" type="password" autocomplete="current-password" placeholder="Password"><button>Unlock</button><span></span></form>';
    f = p.getElementsByTagName('form')[0];
    e = f.elements;
    m = p.getElementsByTagName('span')[0];
    t = o.target || location.pathname;
    e.user.value = d.user || 'admin';
    m.textContent = o.message || '';
    return new Promise(function (resolve, reject) {
      f.onsubmit = function (ev) {
        ev.preventDefault();
        var n = {user: e.user.value || 'admin', pass: e.pass.value || ''};
        af(t, o.request || {}, n).then(function (r) {
          if (r.status === 401) {
            m.textContent = 'Access denied';
            return;
          }
          save(n);
          var k = key(t);
          if (k) challenged[k] = true;
          if (o.ok) {
            rm(p);
            resolve(o.ok(r, n));
            return;
          }
          r.text().then(function (body) {
            if ((r.headers.get('content-type') || '').indexOf('text/html') >= 0) {
              document.open();
              document.write(body);
              document.close();
            } else {
              p.removeAttribute('id');
              p.innerHTML = '<pre></pre>';
              p.getElementsByTagName('pre')[0].textContent = body;
            }
            resolve(r);
          });
        }).catch(function (err) {
          m.textContent = 'Request failed';
          reject(err);
        });
      };
      document.body.appendChild(p);
      e.pass.focus();
    });
  }
  function ready(fn) {
    if (document.body) fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  var ss = document.getElementsByTagName('script');
  var me = document.currentScript || ss[ss.length - 1];
  var boot = me && me.getAttribute('data-micros-auth');
  window.micrOSAuth = {load: load, save: save, clear: clear, headers: hdr, fetch: gf, prompt: prompt};
  if (rf) window.fetch = gf;
  if (boot) ready(function () { prompt({target: boot === '1' ? location.pathname : boot}); });
})();
