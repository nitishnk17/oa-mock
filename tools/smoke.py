#!/usr/bin/env python3
"""Quick check that the app starts, serves its pages and grades an answer (used by the PR check).

    python3 tools/smoke.py
"""
import json, os, sys, threading, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "app"))
from server import data, grading, server  # noqa: E402


def main():
    srv = server.serve(18765)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % port
    def get(path, token=False):
        req = urllib.request.Request(base + path, headers={"X-Token": server.TOKEN} if token else {})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8")
    keys = [k for k, _, _ in data.companies()]
    assert keys, "no companies in data/"
    for path in ["/", "/contribute", "/" + keys[0], "/api/companies/%s/data.js" % keys[0], "/static/js/landing.js",
                 "/static/js/install.js", "/static/css/install.css", "/static/js/exam/langpick.js", "/static/llm-prompt.md"]:
        code, body = get(path)
        assert code == 200 and body, path
        print("ok  GET", path)
    code, body = get("/api/library", token=True)
    assert "companies" in json.loads(body)
    print("ok  GET /api/library")
    code, body = get("/api/toolchain", token=True)
    tc = json.loads(body)
    assert set(tc["langs"]) == {"cpp", "java"} and "job" in tc
    print("ok  GET /api/toolchain (C++ %s, Java %s)" % tuple("here" if tc["langs"][l]["ok"] else "missing" for l in ("cpp", "java")))
    p = data.load(keys[0])
    q = next((q for q in p["questions"] if q.get("type", "code") == "code" and q.get("ref")), None)
    if q:
        d = (q.get("driver") or {}).get("py")
        ref = d["pre"] + q["ref"] + d["post"] if d else q["ref"]     # the page wraps LeetCode-style code the same way
        res = grading.grade(keys[0], q["id"], "py", ref, "all")
        bad = [r for r in res.get("results", []) if not r["ok"]]
        assert "compile_error" not in res and not bad, "reference of %s/%s fails: %s" % (keys[0], q["id"], (res.get("compile_error") or bad[:1]))
        print("ok  graded %s/%s: %d/%d" % (keys[0], q["id"], len(res["results"]), len(res["results"])))
    srv.shutdown()
    print("smoke test passed")


if __name__ == "__main__":
    main()
