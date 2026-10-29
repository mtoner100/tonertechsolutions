#!/usr/bin/env python3
"""Turn the published Newport Apartment Hunt artifact into the read-only page at /apartment-hunt/.

Usage: python3 scripts/patch_page.py <exported-artifact.html> [out.html]

Each replacement must match exactly once. If the artifact's source changes shape
the script stops instead of writing a half-patched page.
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

    # Title and description belong in <head>; the artifact runtime put them in <body>.
    rep("<title>Newport Apartment Hunt</title>\n", "")
    rep("</head><body>",
        '<title>Newport Apartment Hunt</title>'
        '<meta name="description" content="A read-only snapshot of the Newport and Middletown apartment search Matt Toner built with Claude.">'
        '<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">'
        "</head><body>")

    # The read-only runtime must exist before the page script boots.
    rep("<script>\n(function(){", '<script src="runtime.js"></script>\n<script>\n(function(){')

    # Visitors cannot add listings, so drop that tab and soften the board hint.
    rep('    <button role="tab" data-view="add">Add a listing</button>\n', "")
    rep("Drag cards between lanes; drop one on Passed on to pass, drag it back out to revive it. "
        "Click a card to set who leads it, action items, notes and tours.",
        "A read-only view of the board. Click a card to see who leads it, action items, notes and tours.")

    # Both write paths stop at the door.
    rep("async saveUser(id, user){ const cur = state.listings.get(id) || {id};",
        "async saveUser(id, user){ if(window.__READONLY__){ toast('This is a read-only copy of the hunt'); return false; } "
        "const cur = state.listings.get(id) || {id};")
    rep("async addRequest(url, note){ const id = 'r' + uid().slice(1);",
        "async addRequest(url, note){ if(window.__READONLY__) throw new Error('this is a read-only copy of the hunt'); "
        "const id = 'r' + uid().slice(1);")

    # Status pill and the Agents-view connection note describe the snapshot instead of sync.
    rep("  else setStatus('warn', (state.meta.updated_at ? 'Data as of ' + ago(state.meta.updated_at) : 'No data yet') "
        "+ ' · open in the Claude desktop app on your Mac to sync');",
        "  else if(window.__READONLY__) setStatus('ok', 'Snapshot from ' + snapshotDate() + ' · read-only');\n"
        "  else setStatus('warn', (state.meta.updated_at ? 'Data as of ' + ago(state.meta.updated_at) : 'No data yet') "
        "+ ' · open in the Claude desktop app on your Mac to sync');")
    rep("const conn = HUB ? 'Live on this Mac; no sync needed.' :",
        "const conn = window.__READONLY__ ? 'This is a public, read-only snapshot taken ' + snapshotDate() + "
        "'. The live hunt syncs on Matt\\'s Mac through the Claude desktop app.' : HUB ? 'Live on this Mac; no sync needed.' :")
    rep("function ago(iso)",
        "function snapshotDate(){ const at = window.__SNAPSHOT_AT__ || (state.meta && state.meta.updated_at); "
        "try { return new Date(at).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'}); } "
        "catch(e){ return 'today'; } }\nfunction ago(iso)")
    rep("setStatus('warn', 'Open this page on claude.ai or at http://localhost:8790 on your Mac')",
        "setStatus('warn', 'The snapshot runtime did not load')")

    # A way back to the gallery.
    rep('<div class="status" id="status">',
        '<a class="btn small quiet" href="../" style="margin-left:auto">matttoner.ai</a>'
        '<div class="status" id="status" style="margin-left:0">')

    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"wrote {os.path.relpath(dst)} ({os.path.getsize(dst) // 1024} KB)")


if __name__ == "__main__":
    main()
