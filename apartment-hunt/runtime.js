/* Read-only stand-in for Claude's artifact runtime.
 * On claude.ai the page calls window.claude.use('db') and subscribes to a shared
 * database. Here the same calls are answered from data.json, a snapshot taken when
 * the site was last published. Writes are refused; downloads still work. */
(function () {
  'use strict';
  window.__READONLY__ = true;

  var dataPromise = null;
  function load() {
    if (!dataPromise) {
      dataPromise = fetch('data.json', { cache: 'no-cache' }).then(function (r) {
        if (!r.ok) throw new Error('data.json returned ' + r.status);
        return r.json();
      }).then(function (d) {
        window.__SNAPSHOT_AT__ = d.exported_at;
        return d;
      });
    }
    return dataPromise;
  }

  function snap(id, obj) {
    var exists = obj !== undefined && obj !== null;
    return { id: id, exists: exists, data: function () { return obj; } };
  }
  function readOnly() {
    var e = new Error('this is a read-only copy');
    e.code = 'permission_denied';
    return e;
  }
  function lookup(data, path) {
    var parts = path.split('/');
    var col = data[parts[0]] || {};
    return col[parts[1]];
  }
  function fail(err, e) { if (err) err({ code: 'unavailable', message: e && e.message ? e.message : String(e) }); }

  var db = {
    collection: function (name) {
      return {
        onSnapshot: function (cb, err) {
          load().then(function (d) {
            var docs = Object.keys(d[name] || {}).map(function (id) { return snap(id, d[name][id]); });
            cb({ docs: docs, size: docs.length, docChanges: function () { return []; } });
          }).catch(function (e) { fail(err, e); });
          return function () {};
        },
        get: function () {
          return load().then(function (d) {
            var docs = Object.keys(d[name] || {}).map(function (id) { return snap(id, d[name][id]); });
            return { docs: docs, size: docs.length, docChanges: function () { return []; } };
          });
        }
      };
    },
    doc: function (path) {
      var id = path.split('/')[1];
      return {
        onSnapshot: function (cb, err) {
          load().then(function (d) { cb(snap(id, lookup(d, path))); }).catch(function (e) { fail(err, e); });
          return function () {};
        },
        get: function () { return load().then(function (d) { return snap(id, lookup(d, path)); }); },
        set: function () { return Promise.reject(readOnly()); },
        update: function () { return Promise.reject(readOnly()); },
        delete: function () { return Promise.reject(readOnly()); }
      };
    }
  };

  var downloads = {
    save: function (opts) {
      var blob = new Blob([opts.data], { type: opts.mimeType || 'application/octet-stream' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = opts.filename || 'download';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
      return Promise.resolve({ ok: true });
    }
  };

  window.claude = {
    readonly: true,
    use: function (capability) {
      if (capability === 'db') return Promise.resolve(db);
      if (capability === 'downloads') return Promise.resolve(downloads);
      return Promise.resolve(null);
    }
  };
})();
