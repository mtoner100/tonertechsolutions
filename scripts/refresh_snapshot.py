#!/usr/bin/python3
"""Refresh apartment-hunt/data.json from the hub on this Mac and push it if it changed.

The public page talks to the hub live; data.json is only what visitors see while the hub is unreachable.
A launchd job (launchd/com.toner.site-snapshot.plist) runs this every night. Run it by hand any time:

    python3 scripts/refresh_snapshot.py [--no-push]
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

HUB = os.environ.get("HUB_URL", "http://127.0.0.1:8790")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "apartment-hunt", "data.json")
GIT = next((p for p in ("/opt/homebrew/bin/git", "/usr/bin/git") if os.path.exists(p)), "git")
TOKEN_URL = re.compile(r"(https?://[^?#\s\"']+)\?[^#\s\"']*\btoken=[^#\s\"']*", re.I)


def scrub(value):
    if isinstance(value, str):
        return TOKEN_URL.sub(r"\1", value)
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items()}
    return value


def log(msg):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def git(*args, check=True):
    return subprocess.run([GIT, *args], cwd=REPO, check=check, capture_output=True, text=True)


def main():
    push = "--no-push" not in sys.argv
    with urllib.request.urlopen(f"{HUB}/api/state?since=0", timeout=60) as r:
        state = json.load(r)
    listings = {d["id"]: d for d in state.get("listings", []) if d.get("id")}
    requests_ = {d["id"]: d for d in state.get("requests", []) if d.get("id")}
    data = scrub({
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "listings": listings,
        "requests": requests_,
        "meta": {"summary": state.get("meta") or {}, "activity": {"items": state.get("activity") or []},
                 "sync": {"rev": state.get("rev") or 0}},
    })
    if len(listings) < 10:
        sys.exit(f"only {len(listings)} listings came back from the hub; not touching the snapshot")
    body = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    if len(body) > 8_000_000:
        sys.exit(f"snapshot would be {len(body) // 1024} KB; too large, not writing it")

    if push:
        if os.path.exists(OUT):
            git("checkout", "--", os.path.relpath(OUT, REPO))  # drop any stale uncommitted snapshot first
        git("pull", "--rebase", "--quiet")
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    # exported_at always differs; compare everything else
    same = old and json.loads(old).get("listings") == data["listings"] and json.loads(old).get("requests") == data["requests"] \
        and json.loads(old).get("meta", {}).get("summary") == data["meta"]["summary"]
    if same:
        log(f"no change in {len(listings)} listings; snapshot left as is")
        return
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(body)
    log(f"wrote {len(listings)} listings, {len(requests_)} requests, rev {data['meta']['sync']['rev']} ({len(body) // 1024} KB)")
    if not push:
        return
    git("add", "--", os.path.relpath(OUT, REPO))
    git("-c", "commit.gpgsign=false", "commit", "--quiet", "-m",
        f"Nightly snapshot refresh ({len(listings)} listings, rev {data['meta']['sync']['rev']})")
    out = git("push", "--quiet", "origin", "main")
    log("pushed" + (": " + out.stderr.strip() if out.stderr.strip() else ""))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"git {' '.join(e.cmd[1:3])} failed: {e.stderr.strip() or e.stdout.strip()}")
