#!/usr/bin/env python3
"""Checks the specs before (or after) converting: the function-style Python reference, run through the
generated Python driver, must pass every existing test; int-typed values must fit in 32 bits; values
JavaScript reads as numbers must be exact (|x| <= 2^53).

    python3 tools/style/verify.py [company/qid ...]
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path[:0] = [HERE, os.path.join(ROOT, "app")]
from specs import SPECS          # noqa: E402
import convert                   # noqa: E402
from server import judge        # noqa: E402

I32, JS_SAFE = 2**31 - 1, 2**53


def norm(s):
    return "\n".join(l.rstrip() for l in str(s).replace("\r", "").split("\n")).strip("\n")


def token_types(spec):
    """Type of each input token in order, for range checks; None for strings."""
    def walk(tokens):
        p = 0; env = {}
        for it in spec["read"]:
            if it[0] == "rows":
                L = int(eval(str(it[1]), {}, env)) if isinstance(it[1], str) else it[1]
                for _ in range(L):
                    for n, t in it[2]:
                        yield t, tokens[p]; p += 1
                continue
            n, t = it[0], it[1]
            if t in ("int", "long", "str"):
                yield t, tokens[p]
                if t != "str": env[n] = int(tokens[p])
                p += 1
            elif t == "line":
                return
            elif t.endswith("[]") and not t.endswith("[][]"):
                L = int(eval(str(it[2]), {}, env)) if isinstance(it[2], str) else it[2]
                for _ in range(L): yield t[:-2], tokens[p]; p += 1
            elif t == "int[][]":
                R = int(eval(str(it[2]), {}, env)) if isinstance(it[2], str) else it[2]
                C = int(eval(str(it[3]), {}, env)) if isinstance(it[3], str) else it[3]
                for _ in range(R * C): yield "int", tokens[p]; p += 1
    return walk


def load_q(key):
    company, qid = key.split("/")
    with open(os.path.join(ROOT, "data", company, "questions", qid + ".json"), encoding="utf-8") as f:
        return json.load(f)


def main(keys):
    bad = 0
    for key in keys or SPECS:
        q = load_q(key)
        bad += check(key, convert.spec_for(key, q), q)
    print("\n" + ("all specs verified" if not bad else "%d problem(s)" % bad))
    return 1 if bad else 0


def check(key, spec, q):
    """Prints one line for the question; returns 1 if there's a problem."""
    if True:
        bad = 0
        tests = q["samples"] + q["hidden"]
        stub, driver = convert.build(spec)
        src = driver["py"]["pre"] + "class Solution:" + spec["ref"] + driver["py"]["post"]
        res = judge.judge("py", src, [t["in"] for t in tests], 20000)
        if "compile_error" in res:
            print("FAIL %-20s %s" % (key, res["compile_error"][-400:])); return 1
        fails = [i for i, (t, r) in enumerate(zip(tests, res["results"])) if r["tle"] or r["err"] or norm(r["out"]) != norm(t["out"])]
        # ranges
        warn = []
        walk = token_types(spec)
        for t in tests:
            for typ, tok in walk(t["in"].split()):
                if typ in ("int", "long"):
                    v = int(tok)
                    if typ == "int" and abs(v) > I32: warn.append("input %s > int32: use long" % tok); break
                    if abs(v) > JS_SAFE: warn.append("input %s too big for JS numbers" % tok); break
        base = convert.ret_base(spec["ret"])
        if base in ("int", "int[]", "int[][]", "long", "long[]"):
            for t in tests:
                for tok in t["out"].split():
                    try: v = int(tok)
                    except ValueError: continue
                    if base.startswith("int") and abs(v) > I32: warn.append("output %s > int32: return long" % tok); break
                    if abs(v) > JS_SAFE: warn.append("output %s too big for JS numbers" % tok); break
        msg = "ok  " if not fails and not warn else "FAIL"
        bad += bool(fails or warn)
        slow = max(r["ms"] for r in res["results"])
        print("%s %-20s %2d/%d tests  max %5.0f ms  %s%s" % (msg, key, len(tests) - len(fails), len(tests), slow,
              ("failing: %s " % fails[:5]) if fails else "", "; ".join(sorted(set(warn))[:3])))
        if fails:
            r = res["results"][fails[0]]
            print("      first failure  got: %r  expected: %r  err: %s" % (r["out"][:80], tests[fails[0]]["out"][:80], r["err"][-300:]))
        return bad


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
