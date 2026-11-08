"""Grades a submission on the server: runs the question's tests and compares the output.

The browser no longer receives hidden tests with the page. For C++, Java and Python it sends only the
code here; for JavaScript, SQL and the debugging repo (graded in the browser) it fetches the hidden tests
on Submit from /api/companies/<company>/questions/<id>/tests.
"""
from . import data, judge

LIMIT_MS = {"py": 5000, "cpp": 2000, "java": 4000}   # same limits the page uses
PREVIEW = 4000                                         # characters of input / output sent back per test


def norm(s):
    """Same comparison as the page: ignore trailing spaces on each line and blank lines at either end."""
    lines = [l.rstrip() for l in str(s).replace("\r", "").split("\n")]
    return "\n".join(lines).strip("\n")


def preview(s):
    s = str(s)
    return s if len(s) <= PREVIEW else s[:PREVIEW] + "\n… truncated, %d more characters" % (len(s) - PREVIEW)


class GradeError(ValueError):
    pass


def tests_of(company, qid):
    q = data.question(company, qid)
    if q is None:
        raise GradeError("no such question")
    return q


def grade(company, qid, lang, code, scope):
    """scope: "samples" (Run) or "all" (Submit). Returns {compile_error} or {results: [...]}, one per test."""
    if lang not in LIMIT_MS:
        raise GradeError("this language is graded in the browser")
    q = tests_of(company, qid)
    if q.get("type", "code") != "code":
        raise GradeError("this question is graded in the browser")
    tests = q["samples"] + (q.get("hidden", []) if scope == "all" else [])
    res = judge.judge(lang, code, [t["in"] for t in tests], LIMIT_MS[lang])
    if "compile_error" in res:
        return res
    out = []
    for i, (t, r) in enumerate(zip(tests, res["results"])):
        ok = not r["tle"] and not r["err"] and norm(r["out"]) == norm(t["out"])
        kind = "Time limit exceeded" if r["tle"] else "Runtime error" if r["err"] else "Passed" if ok else "Wrong answer"
        out.append({"ok": ok, "kind": kind, "ms": r["ms"], "out": preview(r["out"]), "err": preview(r["err"]),
                    "in": preview(t["in"]), "expected": preview(t["out"]), "sample": i < len(q["samples"])})
    return {"results": out, "samples": len(q["samples"])}
