#!/usr/bin/env python3
"""Merge an export of the Newport Apartment Hunt database into apartment-hunt/data.json.

Usage: python3 scripts/build_data.py <export-dir> [out.json]

<export-dir> holds listings/*.json, requests/*.json and meta/*.json, one document
per file, as Claude's ArtifactData tool writes them. Every URL that carries an
access token in its query string is cut back to its path before publishing.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

TOKEN_URL = re.compile(r"(https?://[^?#\s\"']+)\?[^#\s\"']*\btoken=[^#\s\"']*", re.I)


def scrub(value):
    if isinstance(value, str):
        return TOKEN_URL.sub(r"\1", value)
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items()}
    return value


def load_dir(path):
    docs = {}
    if not os.path.isdir(path):
        return docs
    for name in sorted(os.listdir(path)):
        if name.endswith(".json"):
            with open(os.path.join(path, name), encoding="utf-8") as fh:
                docs[name[:-5]] = json.load(fh)
    return docs


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "apartment-hunt", "data.json")
    data = scrub({
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "listings": load_dir(os.path.join(src, "listings")),
        "requests": load_dir(os.path.join(src, "requests")),
        "meta": load_dir(os.path.join(src, "meta")),
    })
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(data, fh, separators=(",", ":"), ensure_ascii=False)
    print(f"{len(data['listings'])} listings, {len(data['requests'])} requests, "
          f"meta: {', '.join(data['meta']) or 'none'} -> {os.path.relpath(dst)} ({os.path.getsize(dst) // 1024} KB)")


if __name__ == "__main__":
    main()
