#!/usr/bin/env python3
"""Writes data/catalog.json: one entry per company (name, tagline, question count, years, roles, colleges,
size on disk, about how much a download is). The home page uses it to describe companies you haven't downloaded yet.

    python3 tools/build_catalog.py           # rewrite it
    python3 tools/build_catalog.py --check   # exit 1 if it's out of date (for the PR check)

Run it after adding or changing questions; commit the result with them.
"""
import json, os, subprocess, sys, zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "catalog.json")


def entry(key):
    d = os.path.join(DATA, key)
    with open(os.path.join(d, "company.json"), encoding="utf-8") as f:
        c = json.load(f)
    qs = []
    for name in sorted(os.listdir(os.path.join(d, "questions"))):
        if name.endswith(".json"):
            with open(os.path.join(d, "questions", name), encoding="utf-8") as f:
                qs.append(json.load(f))
    files = [os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs]
    size = sum(os.path.getsize(f) for f in files)
    packed = sum(len(zlib.compress(open(f, "rb").read(), 6)) for f in files)   # about what git downloads
    vals = lambda k: sorted({q[k] for q in qs if q.get(k)}, key=lambda v: (-v if isinstance(v, int) else 0, str(v)))
    return {
        "key": key, "name": c.get("name", key), "tagline": c.get("tagline", ""),
        "questions": len(qs), "years": vals("year"), "roles": vals("role"), "colleges": vals("college"),
        "formats": [f["name"] for k, f in c.get("formats", {}).items() if k != "custom"],
        "bytes": size, "download": packed,
    }


def _in_git(key):
    """Is data/<key> in the repository? (A slim clone has only some companies on disk; keep the others' entries.)"""
    try:
        return subprocess.run(["git", "-C", ROOT, "cat-file", "-e", "HEAD:data/" + key],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except OSError:
        return True


def build():
    keys = sorted(k for k in os.listdir(DATA) if os.path.isfile(os.path.join(DATA, k, "company.json")))
    entries = {k: entry(k) for k in keys}
    if os.path.isfile(OUT):
        with open(OUT, encoding="utf-8") as f:
            for c in json.load(f).get("companies", []):
                if c["key"] not in entries and _in_git(c["key"]):
                    entries[c["key"]] = c
    return {"version": 1, "companies": [entries[k] for k in sorted(entries)]}


if __name__ == "__main__":
    cat = build()
    text = json.dumps(cat, indent=1, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        old = open(OUT, encoding="utf-8").read() if os.path.isfile(OUT) else ""
        if old != text:
            print("data/catalog.json is out of date: run python3 tools/build_catalog.py and commit it"); sys.exit(1)
        print("catalog up to date"); sys.exit(0)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    for c in cat["companies"]:
        print("%-10s %3d questions  %5.1f MB (download %4.1f MB)  years %s" % (c["key"], c["questions"], c["bytes"] / 1e6, c.get("download", 0) / 1e6, c["years"] or "-"))
