/* Connects the Newport Apartment Hunt page to the hub on Matt's Mac.
 *
 * The page was written with a "hub" mode for http://localhost:8790. Here that mode is pointed at the hub's public
 * address, reached through a Cloudflare Tunnel. Anyone can read. Editing needs a sign-in: Cloudflare Access checks
 * the person's email with a one-time code, and the hub issues a session cookie. If the hub cannot be reached, the
 * page falls back to data.json, a snapshot taken when the site was last published. */
(function () {
  'use strict';

  var BASE = 'https://hub.tonertechsolutions.com';
  var local = location.hostname === 'localhost' || location.hostname === '127.0.0.1';
  if (local) {
    // Previewing the site on this Mac: talk to the hub here. ?hub=http://localhost:8791 points at a test hub.
    var override = new URLSearchParams(location.search).get('hub');
    BASE = override || ('http://' + location.hostname + ':8790');
  }
  window.__HUB__ = { remote: true, base: BASE };
  window.__READONLY__ = true;

  // ---- snapshot fallback, in the shape the page's applyPull() expects
  var dataPromise = null;
  function loadData() {
    if (!dataPromise) {
      dataPromise = fetch('data.json', { cache: 'no-cache' }).then(function (r) {
        if (!r.ok) throw new Error('data.json returned ' + r.status);
        return r.json();
      }).then(function (d) { window.__SNAPSHOT_AT__ = d.exported_at; return d; });
    }
    return dataPromise;
  }
  function values(obj) { return Object.keys(obj || {}).map(function (k) { return obj[k]; }); }
  window.__SNAPSHOT__ = function () {
    return loadData().then(function (d) {
      var meta = d.meta || {};
      return { rev: (meta.sync || {}).rev || 0, listings: values(d.listings), deleted: [], requests: values(d.requests),
               meta: meta.summary || {}, activity: (meta.activity || {}).items || [], full: true };
    });
  };

  // ---- sign-in
  var authEl = document.getElementById('auth');
  var tabAdd = document.getElementById('tab-add');
  var hint = document.getElementById('board-hint');
  var fullHint = hint ? hint.textContent : '';
  var me = null;
  var hubDown = false;  // no point offering sign-in while the hub cannot be reached

  function toast(msg) {
    var root = document.getElementById('toast-root');
    if (!root) return;
    var el = document.createElement('div');
    el.className = 'toast';
    el.textContent = msg;
    root.innerHTML = '';
    root.appendChild(el);
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 2600);
  }
  function loginUrl() { return BASE + '/api/login?next=' + encodeURIComponent(location.href.split('#')[0] + location.hash); }

  function render() {
    if (!authEl) return;
    authEl.innerHTML = '';
    if (me && me.editor) {
      var who = document.createElement('span');
      who.textContent = me.local ? 'Editing from this Mac' : 'Signed in as ' + (me.name || me.email);
      authEl.appendChild(who);
      if (!me.local) {
        var out = document.createElement('button');
        out.className = 'btn small quiet';
        out.textContent = 'Sign out';
        out.addEventListener('click', function () {
          fetch(BASE + '/api/logout', { method: 'POST', credentials: 'include' }).catch(function () {}).then(function () { setMe(null); toast('Signed out'); });
        });
        authEl.appendChild(out);
      }
    } else if (!hubDown) {
      var a = document.createElement('a');
      a.className = 'btn small';
      a.id = 'sign-in';
      a.href = loginUrl();
      a.textContent = 'Sign in to edit';
      authEl.appendChild(a);
    }
  }
  function setMe(who) {
    me = who && who.editor ? who : null;
    window.__READONLY__ = !me;
    if (tabAdd) tabAdd.hidden = !me;
    if (hint) hint.textContent = me ? fullHint : 'Read-only until you sign in. Click a card to see who leads it, action items, notes and tours.';
    render();
  }
  window.__requireSignIn = function () {
    toast('Sign in to edit (top right)');
    var btn = document.getElementById('sign-in');
    if (btn) { btn.classList.add('primary'); setTimeout(function () { btn.classList.remove('primary'); }, 1800); }
  };
  window.__signedOut = function () { setMe(null); };

  setMe(null);
  fetch(BASE + '/api/me', { credentials: 'include' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(setMe)
    .catch(function () { hubDown = true; setMe(null); });
})();
