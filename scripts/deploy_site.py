#!/usr/bin/env python3
"""Publish the current dashboard to https://tonertechsolutions.com/apartment-hunt/.

    python3 scripts/deploy_site.py [--no-push] [--no-wait]

Reads ~/agents/apartments/web/dashboard.html, wraps it the way a claude.ai artifact export is wrapped, runs
patch_page.py (sign-in, the hub's public address, the snapshot fallback), commits apartment-hunt/index.html, pushes
to GitHub Pages, waits until the site serves the new page version, and records that version in
~/agents/apartments/data/site-build.json so the hub can tell open pages to reload.
Run it after every change to the dashboard; the claude.ai artifact is published separately."""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATCH = os.path.join(REPO, "scripts", "patch_page.py")
OUT = os.path.join(REPO, "apartment-hunt", "index.html")
DASH = os.path.expanduser("~/agents/apartments/web/dashboard.html")
BUILD_FILE = os.path.expanduser("~/agents/apartments/data/site-build.json")
SITE_URL = "https://tonertechsolutions.com/apartment-hunt/"
GIT = next((p for p in ("/opt/homebrew/bin/git", "/usr/bin/git") if os.path.exists(p)), "git")
# the skeleton the Artifact tool puts around the page; patch_page.py expects this shape
HEAD = ('<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'html{scroll-padding-top:env(safe-area-inset-top,0px)}body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}'
        'img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style></head><body>')


def log(msg):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def git(*args, check=True):
    return subprocess.run([GIT, *args], cwd=REPO, check=check, capture_output=True, text=True)


def served_build():
    req = urllib.request.Request(f"{SITE_URL}?nocache={int(time.time())}", headers={"Cache-Control": "no-cache", "Pragma": "no-cache"})
    with urllib.request.urlopen(req, timeout=30) as r:
        m = re.search(r"const BUILD = '(v\d+)'", r.read().decode("utf-8", "replace"))
    return m.group(1) if m else None


def main():
    push, wait = "--no-push" not in sys.argv, "--no-wait" not in sys.argv
    if push:
        git("pull", "--rebase", "--autostash", "--quiet")  # pick up the nightly snapshot commits before building
    dash = open(DASH, encoding="utf-8").read()
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
        tmp.write(HEAD + dash + "</body></html>")
    try:
        subprocess.run([sys.executable, PATCH, tmp.name, OUT], check=True)
    finally:
        os.unlink(tmp.name)
    out = open(OUT, encoding="utf-8").read()
    m = re.search(r"const BUILD = '(v\d+)'", out)
    if not m or 'src="runtime.js"' not in out:
        sys.exit("the patched page has no BUILD marker or no runtime.js; not publishing it")
    build = m.group(1)
    log(f"built apartment-hunt/index.html as {build} ({len(out) // 1024} KB)")
    if not push:
        return
    git("add", "--", "apartment-hunt/index.html", "scripts")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        log("nothing new to commit")
    else:
        git("-c", "commit.gpgsign=false", "commit", "--quiet", "-m",
            f"Apartment hunt page {build}\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>")
        git("push", "--quiet", "origin", "main")
        log("pushed to GitHub; Pages usually serves it within a minute or two")
    if wait:
        deadline = time.time() + 8 * 60
        while time.time() < deadline:
            try:
                have = served_build()
            except Exception as e:
                have = f"error: {e}"
            if have == build:
                break
            log(f"site serves {have}; waiting for {build}")
            time.sleep(20)
        else:
            sys.exit(f"the site still does not serve {build} after 8 minutes; check GitHub Pages")
        log(f"the site serves {build}")
    os.makedirs(os.path.dirname(BUILD_FILE), exist_ok=True)
    with open(BUILD_FILE, "w", encoding="utf-8") as fh:
        json.dump({"build": build, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "url": SITE_URL}, fh)
    log(f"recorded {build} in {BUILD_FILE}; open pages will offer a reload")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"git {' '.join(e.cmd[1:3])} failed: {e.stderr.strip() or e.stdout.strip()}")
