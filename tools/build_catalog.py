#!/usr/bin/env python3
"""Writes data/catalog.json: one entry per company (name, tagline, question count, years, roles, colleges,
size on disk, about how much a download is). The home page uses it to describe companies you haven't downloaded yet.

    python3 tools/build_catalog.py           # rewrite it
    python3 tools/build_catalog.py --check   # exit 1 if it's out of date (for the PR check)

Run it after adding or changing questions; commit the result with them.
"""
import base64, bz2, json, os, subprocess, sys

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
    blobs = [open(f, "rb").read().replace(b"\r\n", b"\n") for f in files]   # as git stores them (Windows checks out CRLF)
    size = sum(len(b) for b in blobs)
    # about what git downloads. bzip2 (unchanged since 2010) rather than zlib, whose output differs between
    # builds (zlib vs zlib-ng), so every computer and GitHub's runner get the same number; x1.1 matches git.
    packed = round(sum(len(bz2.compress(b, 9)) for b in blobs) * 1.1 / 1000) * 1000
    vals = lambda k: sorted({q[k] for q in qs if q.get(k)}, key=lambda v: (-v if isinstance(v, int) else 0, str(v)))
    return {
        "key": key, "name": c.get("name", key), "tagline": c.get("tagline", ""),
        "questions": len(qs), "years": vals("year"), "roles": vals("role"), "colleges": vals("college"),
        "formats": [f["name"] for k, f in c.get("formats", {}).items() if k != "custom"],
        "bytes": size, "download": packed, **_logo(d, c),
    }


LOGO_TYPES = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp"}
LOGO_MAX = 24 * 1024


def _logo(d, c):
    """Optional "logo" in company.json: a file next to it (logo.svg / .png / .webp, at most 24 KB), embedded in the
    catalog so the home page can show it before the company is downloaded. Without one the page shows a monogram."""
    name = c.get("logo")
    if not name:
        return {}
    ext = os.path.splitext(name)[1].lower()
    path = os.path.join(d, name)
    if "/" in name or "\\" in name or ext not in LOGO_TYPES or not os.path.isfile(path):
        raise SystemExit("%s: \"logo\" must be a .svg, .png or .webp file next to company.json" % d)
    raw = open(path, "rb").read()
    if len(raw) > LOGO_MAX:
        raise SystemExit("%s: the logo is %d KB; keep it under %d KB" % (name, len(raw) // 1024, LOGO_MAX // 1024))
    return {"logo": "data:%s;base64,%s" % (LOGO_TYPES[ext], base64.b64encode(raw).decode("ascii"))}


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
