# matttoner.ai

A static site that publishes pages built with Claude. Hosted on GitHub Pages from this repository; nothing here needs a build step or a server.

## Layout

| Path | What it is |
|---|---|
| `index.html` | The gallery home page. Each published page is one card. |
| `assets/` | Shared stylesheet and favicon. |
| `apartment-hunt/index.html` | The Newport Apartment Hunt page, patched to run read-only. |
| `apartment-hunt/data.json` | A snapshot of the hunt's database: listings, requests, summary, activity. |
| `apartment-hunt/runtime.js` | A stand-in for Claude's artifact runtime that serves `data.json` and refuses writes. |
| `scripts/build_data.py` | Rebuilds `data.json` from a database export. |
| `scripts/patch_page.py` | Rebuilds `apartment-hunt/index.html` from a fresh export of the artifact. |
| `CNAME` | The custom domain GitHub Pages answers on. |
| `.nojekyll` | Tells GitHub Pages to serve files as they are. |

## Preview locally

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open <http://127.0.0.1:8000/>.

## Refresh the apartment hunt

The data is a snapshot, so the public page only changes when it is rebuilt. Ask Claude to:

1. Export the artifact's `listings`, `requests` and `meta` collections to a folder.
2. Run `python3 scripts/build_data.py <that-folder>`.
3. Commit and push.

If the page itself changed on claude.ai, also export the artifact's HTML and run `python3 scripts/patch_page.py <exported.html>`.

## Add another page

1. Put it in its own folder with an `index.html`.
2. Add a card for it in `index.html`.
3. Commit and push.

## DNS for matttoner.ai

Set these at the registrar after buying the domain.

| Type | Host | Value |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `mtoner100.github.io` |

Then in the repository's Settings → Pages set the custom domain to `matttoner.ai` and turn on Enforce HTTPS once the check passes.
