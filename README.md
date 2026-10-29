# tonertechsolutions.com

A static site that publishes pages built with Claude. Hosted on GitHub Pages from this repository; nothing here needs a build step or a server.

## Layout

| Path | What it is |
|---|---|
| `index.html` | The gallery home page. Each published page is one card. |
| `assets/` | Shared stylesheet and favicon. |
| `apartment-hunt/index.html` | The Newport Apartment Hunt page, patched to talk to the hub through the tunnel. |
| `apartment-hunt/data.json` | Fallback snapshot of the hunt's database, used only when the hub is unreachable. |
| `apartment-hunt/runtime.js` | Points the page at the hub, handles sign-in, and loads `data.json` as a fallback. |
| `scripts/build_data.py` | Rebuilds `data.json` from a database export. |
| `scripts/patch_page.py` | Rebuilds `apartment-hunt/index.html` from a fresh export of the artifact. |
| `CNAME` | The custom domain GitHub Pages answers on. |
| `.nojekyll` | Tells GitHub Pages to serve files as they are. |

## Preview locally

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open <http://127.0.0.1:8000/>.

## How the apartment hunt page works

The page is the same dashboard that runs on Matt's Mac, pointed at the hub's public address,
`hub.tonertechsolutions.com`, which a Cloudflare Tunnel connects to the hub. Anyone can read. Editing needs a sign-in:
Cloudflare Access checks the person's email with a one-time code, and the hub issues a session cookie. If the hub
cannot be reached, the page falls back to `apartment-hunt/data.json`, a snapshot taken when the site was last
published, and says so in the header.

To refresh that fallback snapshot, ask Claude to export the hub's data and run
`python3 scripts/build_data.py <that-folder>`, then commit and push. If the page itself changed, also export the
artifact's HTML and run `python3 scripts/patch_page.py <exported.html>`.

## Add another page

1. Put it in its own folder with an `index.html`.
2. Add a card for it in `index.html`.
3. Commit and push.

## DNS for tonertechsolutions.com

Set these at the registrar after buying the domain.

| Type | Host | Value |
|---|---|---|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `mtoner100.github.io` |

Then in the repository's Settings → Pages set the custom domain to `tonertechsolutions.com` and turn on Enforce HTTPS once the check passes.
