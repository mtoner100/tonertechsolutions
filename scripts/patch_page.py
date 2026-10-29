#!/usr/bin/env python3
"""Turn the published Newport Apartment Hunt artifact into the live page served at /apartment-hunt/.

Usage: python3 scripts/patch_page.py <exported-artifact.html> [out.html]

The page keeps its own "hub" mode, written for http://localhost:8790 on Matt's Mac. These patches point that mode at
the public hub address (set in runtime.js), add sign-in, and fall back to data.json when the hub is unreachable.
Each replacement must match exactly once; if the artifact's source changes shape the script stops.
"""
import os
import sys


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "apartment-hunt", "index.html")
    with open(src, encoding="utf-8") as fh:
        html = fh.read()

    def rep(old, new):
        nonlocal html
        n = html.count(old)
        if n != 1:
            sys.exit(f"expected exactly one match for {old[:70]!r}, found {n}")
        html = html.replace(old, new)

    # <head>: title, description, icon
    rep("<title>Newport Apartment Hunt</title>\n", "")
    rep("</head><body>",
        '<title>Newport Apartment Hunt</title>'
        '<meta name="description" content="The Newport and Middletown apartment search Matt Toner runs with Claude agents: live listings, board, map and tours.">'
        '<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">'
        "</head><body>")

    # a little styling for the sign-in area
    rep(".toast{position:fixed;", ".auth{display:inline-flex;align-items:center;gap:8px;font-size:12px;color:var(--muted);white-space:nowrap}\n.toast{position:fixed;")

    # runtime.js sets window.__HUB__ before the page script boots
    rep("<script>\n(function(){", '<script src="runtime.js"></script>\n<script>\n(function(){')

    # header: a way back to the site, and a place for sign-in
    rep('<div class="status" id="status">',
        '<a class="btn small quiet" href="../" style="margin-left:auto">tonertechsolutions.com</a>'
        '<div class="status" id="status" style="margin-left:0">')
    rep('<button class="btn small" id="sync-btn" hidden>Sync now</button></div>',
        '<button class="btn small" id="sync-btn" hidden>Sync now</button></div><span class="auth" id="auth"></span>')

    # the Add tab and the board hint show up for signed-in editors
    rep('<button role="tab" data-view="add">Add a listing</button>',
        '<button role="tab" data-view="add" id="tab-add" hidden>Add a listing</button>')
    rep('<div class="toolbar"><h2>Your board</h2><span class="muted small">Drag cards between lanes;',
        '<div class="toolbar"><h2>Your board</h2><span class="muted small" id="board-hint">Drag cards between lanes;')

    # hub mode can be remote
    rep("const HUB = !!(window.__HUB__ && window.__HUB__.local);",
        "const HUB = !!(window.__HUB__ && (window.__HUB__.local || window.__HUB__.remote));\n"
        "const HUB_REMOTE = !!(window.__HUB__ && window.__HUB__.remote);\n"
        "const HUB_BASE = (window.__HUB__ && window.__HUB__.base) || '';")

    rep("  async poll(first){ try { const r = await fetch('/api/state?since=' + (first ? 0 : state.syncRev)); const j = await r.json(); "
        "applyPull(j, true); setStatus('ok', 'Live on this Mac · ' + ago(j.meta.updated_at)); } "
        "catch(e){ setStatus('bad', 'Hub not reachable: ' + e.message); } },",
        "  async poll(first){ try { const r = await fetch(HUB_BASE + '/api/state?since=' + (first ? 0 : state.syncRev), {credentials: 'include'}); "
        "if(!r.ok) throw new Error('hub answered ' + r.status); const j = await r.json(); this.offline = false; applyPull(j, true); "
        "setStatus('ok', (HUB_REMOTE ? 'Live · data ' : 'Live on this Mac · ') + ago(j.meta.updated_at)); } "
        "catch(e){ if(HUB_REMOTE && window.__SNAPSHOT__ && !state.listings.size){ try { const snap = await window.__SNAPSHOT__(); this.offline = true; "
        "applyPull(snap, true); setStatus('warn', 'Snapshot from ' + snapshotDate() + ' · the hub is offline'); return; } catch(e2){} } "
        "setStatus(this.offline ? 'warn' : 'bad', HUB_REMOTE ? 'Hub not reachable right now' : 'Hub not reachable: ' + e.message); } },")

    rep("  async saveUser(id, user){ const r = await fetch('/api/user', {method:'POST', headers:{'Content-Type':'application/json'}, "
        "body: JSON.stringify({id, user})}); const j = await r.json(); if(j.listing) state.listings.set(id, j.listing); return j.ok; },",
        "  async saveUser(id, user){ if(window.__READONLY__){ if(window.__requireSignIn) window.__requireSignIn(); return false; } "
        "const r = await fetch(HUB_BASE + '/api/user', {method:'POST', credentials: 'include', headers:{'Content-Type':'application/json'}, "
        "body: JSON.stringify({id, user})}); if(r.status === 401){ if(window.__signedOut) window.__signedOut(); toast('Your sign-in expired; sign in again'); return false; } "
        "const j = await r.json(); if(j.listing) state.listings.set(id, j.listing); return j.ok; },")

    rep("  async addRequest(url, note){ const r = await fetch('/api/request', {method:'POST', headers:{'Content-Type':'application/json'}, "
        "body: JSON.stringify({url, note})}); const j = await r.json(); if(j.listing) state.listings.set(j.listing.id, j.listing); await this.poll(false); return j; },",
        "  async addRequest(url, note){ if(window.__READONLY__) throw new Error('sign in to add a listing'); "
        "const r = await fetch(HUB_BASE + '/api/request', {method:'POST', credentials: 'include', headers:{'Content-Type':'application/json'}, "
        "body: JSON.stringify({url, note})}); if(r.status === 401){ if(window.__signedOut) window.__signedOut(); throw new Error('your sign-in expired'); } "
        "const j = await r.json(); if(!r.ok) throw new Error(j.error || ('hub answered ' + r.status)); "
        "if(j.listing) state.listings.set(j.listing.id, j.listing); await this.poll(false); return j; },")

    # the Agents view explains the connection
    rep("const conn = HUB ? 'Live on this Mac; no sync needed.' :",
        "const conn = HUB_REMOTE ? (state.backend && state.backend.offline ? 'The hub on Matt\\'s Mac is offline; this is the snapshot taken ' + snapshotDate() + '.' "
        ": 'Live: this page talks to the hub on Matt\\'s Mac through a Cloudflare Tunnel. Edits reach the agents at once.') "
        ": HUB ? 'Live on this Mac; no sync needed.' :")

    rep("function ago(iso)",
        "function snapshotDate(){ const at = window.__SNAPSHOT_AT__ || (state.meta && state.meta.updated_at); "
        "try { return new Date(at).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'}); } catch(e){ return 'earlier'; } }\n"
        "function ago(iso)")
    rep("setStatus('warn', 'Open this page on claude.ai or at http://localhost:8790 on your Mac')",
        "setStatus('warn', 'The page runtime did not load')")

    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"wrote {os.path.relpath(dst)} ({os.path.getsize(dst) // 1024} KB)")


if __name__ == "__main__":
    main()
