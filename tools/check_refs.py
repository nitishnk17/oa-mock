#!/usr/bin/env python3
"""Runs every question's reference solutions against its sample + hidden tests.

    python3 tools/check_refs.py              # all companies
    python3 tools/check_refs.py amazon       # one company

Uses the same judge as the server (app/server/judge.py). Python and C++ references are
checked; SQL, debugging and SJT questions are skipped (the debugging tests are
generated from the fixed repo by tools/amazon/watchlist/gen_tests.js).
"""
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
from server import data, judge  # noqa: E402


def norm(s):
    return "\n".join(l.rstrip() for l in str(s).replace("\r", "").split("\n")).strip("\n")


def wrap(q, lang, code):
    """Function-style references run inside the question's driver; full-program ones run as they are."""
    if lang == "cpp" and q.get("refcppProgram"):
        return code
    d = (q.get("driver") or {}).get(lang)
    return d["pre"] + code + d["post"] if d else code


def main(keys):
    failed = 0
    for key in keys or [k for k, _, _ in data.companies()]:
        p = data.load(key)
        if p is None:
            print("no such company:", key); failed += 1; continue
        for q in p["questions"]:
            if q.get("type", "code") != "code":
                print("  skip  %-10s %-12s (%s)" % (key, q["id"], q.get("type")))
                continue
            tests = q["samples"] + q["hidden"]
            for lang, field in (("py", "ref"), ("cpp", "refcpp")):
                if not q.get(field):
                    continue
                res = judge.judge(lang, wrap(q, lang, q[field]), [t["in"] for t in tests], 10000)
                if "compile_error" in res:
                    print("  FAIL  %-10s %-12s %-3s compile error:\n%s" % (key, q["id"], lang, res["compile_error"][-800:]))
                    failed += 1; continue
                bad = [i for i, (t, r) in enumerate(zip(tests, res["results"]))
                       if r["tle"] or r["err"] or norm(r["out"]) != norm(t["out"])]
                slow = max(r["ms"] for r in res["results"])
                print("  %s  %-10s %-12s %-3s %d/%d  max %.0f ms" % ("ok  " if not bad else "FAIL", key, q["id"], lang,
                                                                  len(tests) - len(bad), len(tests), slow))
                failed += bool(bad)
    print("\n%s" % ("all reference solutions pass" if not failed else "%d failure(s)" % failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
