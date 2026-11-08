"""Adding a question: check it, save it into data/, and send it as a pull request.

check(company, q)   runs every check the pull-request check runs (tools/add_question.py is the same from a terminal):
                    format, the function spec (generates the LeetCode stub + hidden driver in 4 languages), the
                    reference solutions on every test, the 4 drivers reading every input the same way, known-wrong
                    solutions failing, and duplicates already in the bank.
save(company, q)    writes data/<company>/questions/<id>.json (and company.json for a new company), and refreshes the
                    local catalog.
share(company, qid) commits just those files on top of GitHub's main branch, without touching your working copy,
                    pushes them to your fork with the GitHub CLI (gh) and opens a pull request.
"""
import contextlib, io, json, os, re, subprocess, sys, tempfile, time

from . import data, judge, library

TOOLS = os.path.join(data.ROOT, "tools")
STYLE = os.path.join(TOOLS, "style")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
DIFFS = ("Easy", "Medium", "Hard")
PY_LIMIT = 5000                      # what a Python answer gets on the platform (grading.LIMIT_MS)
MAX_BYTES = 20 * 1024 * 1024


class Problem(ValueError):
    pass


def _tools():
    for p in (STYLE, TOOLS):
        if p not in sys.path:
            sys.path.insert(0, p)
    import convert, verify, selftest, check_dupes, build_catalog   # noqa: E401
    return convert, verify, selftest, check_dupes, build_catalog


def _captured(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*args)
    text = re.sub(r"^(ok  |FAIL) +[a-z0-9_-]+/[a-z0-9_-]+ +", "", buf.getvalue().strip())   # the tools' own line prefix
    return rc, text


def _norm(s):
    return "\n".join(l.rstrip() for l in str(s).replace("\r", "").split("\n")).strip("\n")


def _have_all_languages():
    import shutil
    return bool(judge.GPP and judge.JAVAC and judge.JAVA and shutil.which("node"))


def _tidy(q):
    """Small fixes LLM-written JSON often needs: numbers as strings in tests, stray whitespace in ids."""
    for t in q.get("samples", []) + q.get("hidden", []):
        if isinstance(t, dict):
            for k in ("in", "out"):
                if isinstance(t.get(k), (int, float)):
                    t[k] = str(t[k])
            if isinstance(t.get("in"), str) and not t["in"].endswith("\n"):
                t["in"] += "\n"
    if isinstance(q.get("id"), str):
        q["id"] = q["id"].strip()
    return q


def _format(company, q, replace):
    errs, warns = [], []
    if not data.KEY_RE.match(company or ""):
        errs.append("company key must be lowercase letters, digits, - or _ (e.g. google)")
    if not isinstance(q, dict):
        return ["the question must be one JSON object"], warns
    if not ID_RE.match(q.get("id") or ""):
        errs.append('"id" must be short, lowercase letters, digits, - or _ (e.g. "maxpath")')
    if q.get("type", "code") != "code":
        errs.append('only coding questions ("type": "code") can be checked here; open a pull request by hand for SQL, debugging or SJT')
    for k in ("title", "body", "inp", "out"):
        if not isinstance(q.get(k), str) or not q[k].strip():
            errs.append('"%s" is missing' % k)
    if q.get("diff") not in DIFFS:
        errs.append('"diff" must be Easy, Medium or Hard')
    for k, need in (("samples", 1), ("hidden", 1)):
        ts = q.get(k)
        if not isinstance(ts, list) or len(ts) < need:
            errs.append('"%s" needs at least %d test' % (k, need))
        elif not all(isinstance(t, dict) and isinstance(t.get("in"), str) and isinstance(t.get("out"), str) for t in ts):
            errs.append('every test in "%s" needs "in" and "out" strings' % k)
    if isinstance(q.get("hidden"), list) and 0 < len(q["hidden"]) < 5:
        warns.append("only %d hidden tests; 8-15 that include edge cases and a maximum-size input work best" % len(q["hidden"]))
    if "year" in q and not (isinstance(q["year"], int) and 2000 <= q["year"] <= 2100):
        errs.append('"year" must be a number like 2026')
    if "month" in q and not (isinstance(q["month"], int) and 1 <= q["month"] <= 12):
        errs.append('"month" must be 1-12')
    if "year" not in q:
        warns.append('no "year": add when it was asked if you know it (the bank sorts by year)')
    if not q.get("ref"):
        errs.append('"ref" (a Python reference solution) is missing')
    if not errs and not replace and os.path.exists(os.path.join(data.DATA_DIR, company, "questions", q["id"] + ".json")):
        errs.append('%s already has a question with id "%s"; pick another id' % (company, q["id"]))
    size = len(json.dumps(q))
    if size > MAX_BYTES:
        errs.append("the question is %.0f MB; keep it under 20 MB (fewer or smaller maximum-size tests)" % (size / 1e6))
    return errs, warns


def check(company, q, replace=False):
    """{ok, checks: [{name, status: ok|warn|fail|skip, detail}], question}. question has stub/driver filled in."""
    convert, verify, selftest, check_dupes, _ = _tools()
    checks = []
    add = lambda name, status, detail="": checks.append({"name": name, "status": status, "detail": detail})
    q = _tidy(dict(q)) if isinstance(q, dict) else q
    errs, warns = _format(company, q, replace)
    add("Format", "fail" if errs else "warn" if warns else "ok", "\n".join(errs + warns) or "all fields present")
    if errs:
        return {"ok": False, "checks": checks, "question": q}
    key = "%s/%s" % (company, q["id"])
    tests = q["samples"] + q["hidden"]

    # function spec -> stub + driver
    spec = None
    try:
        spec = convert.spec_for(key, q)
    except Exception as e:
        add("Function spec", "fail", str(e))
    if spec:
        try:
            before = (q.get("stub"), q.get("driver"))
            convert.apply(q, spec)
            if before[0] is not None and before != (q["stub"], q["driver"]):
                add("Generated code up to date", "fail", '"stub"/"driver" in the file don\'t match its "spec". Don\'t edit them by hand: '
                    "save the question again (the app, or tools/add_question.py <company> <file> --save --replace).")
            add("Function spec", "ok", "%s(%s): stub and input/output driver generated for Python, C++, Java and JavaScript"
                % (spec["fn"], ", ".join(n for n, _ in convert.params(spec))))
        except Exception as e:
            add("Function spec", "fail", "%s: %s" % (type(e).__name__, e)); spec = None
    elif not any(c["name"] == "Function spec" for c in checks):
        if q.get("driver"):
            add("Function spec", "warn", 'no "spec": keeping the hand-written stub and driver')
        else:
            add("Function spec", "warn", 'no "spec": the question is a full program (read stdin, print stdout) in both styles. '
                'Add a "spec" to make it LeetCode-style.')

    # reference solutions
    if spec:
        rc, out = _captured(verify.check, key, spec, q)
        add("Python reference", "fail" if rc else "ok", out)
    else:
        src = q["driver"]["py"]["pre"] + q["ref"] + q["driver"]["py"]["post"] if (q.get("driver") or {}).get("py") else q["ref"]
        res = judge.judge("py", src, [t["in"] for t in tests], 20000)
        add("Python reference", *_verdict(res, tests))
    if q.get("refcpp"):
        if not judge.GPP:
            add("C++ reference", "skip", "no C++ compiler here; the pull-request check runs it")
        else:
            src = q["refcpp"] if q.get("refcppProgram") or "int main" in q["refcpp"] else \
                (q.get("driver") or {}).get("cpp", {}).get("pre", "") + q["refcpp"] + (q.get("driver") or {}).get("cpp", {}).get("post", "")
            add("C++ reference", *_verdict(judge.judge("cpp", src, [t["in"] for t in tests], 10000), tests))

    # 4 languages read the input the same way
    if spec:
        if _have_all_languages():
            rc, out = _captured(selftest.check, key, spec, q)
            add("Drivers in 4 languages", "fail" if rc else "ok", out)
        else:
            add("Drivers in 4 languages", "skip", "needs g++, a JDK and node on this computer; the pull-request check runs it")

    # the tests catch wrong answers
    add("Tests catch wrong answers", *_wrong_answers(q, spec))

    # duplicates
    add("Not already in the bank", *_dupes(company, q, check_dupes))

    ok = not any(c["status"] == "fail" for c in checks)
    return {"ok": ok, "checks": checks, "question": q}


def _verdict(res, tests):
    if "compile_error" in res:
        return "fail", "compile error:\n" + res["compile_error"][-1500:]
    bad = [i for i, (t, r) in enumerate(zip(tests, res["results"])) if r["tle"] or r["err"] or _norm(r["out"]) != _norm(t["out"])]
    slow = max(r["ms"] for r in res["results"])
    if bad:
        r, t = res["results"][bad[0]], tests[bad[0]]
        return "fail", "%d/%d tests pass. First failure (test %d): expected %r, got %r %s" % (
            len(tests) - len(bad), len(tests), bad[0] + 1, t["out"][:120], r["out"][:120], r["err"][-300:])
    return "ok", "%d/%d tests pass, slowest %.0f ms" % (len(tests), len(tests), slow)


def _wrong_answers(q, spec):
    hidden = q["hidden"]
    outs = {_norm(t["out"]) for t in hidden}
    if len(outs) == 1 and len(hidden) > 1:
        return "fail", "every hidden test expects %r, so a program that always prints that passes. Add tests with other answers." % next(iter(outs))[:60]
    notes, status = [], "ok"
    biggest = max(len(t["in"]) for t in hidden)
    notes.append("hidden tests have %d different answers; the largest input is %s" % (
        len(outs), "%.0f KB" % (biggest / 1e3) if biggest > 2000 else "%d characters" % biggest))
    wrong = q.get("wrong") or []
    if not wrong:
        status = "warn"
        notes.append('add 1-2 known-wrong solutions in "wrong" (e.g. brute force, off-by-one) to prove the tests catch them')
    for w in wrong:
        if not isinstance(w, dict) or not w.get("ref"):
            notes.append('each "wrong" entry needs "ref" (Python, same shape as "ref") and "why"'); status = "fail"; continue
        code = w["ref"]
        if spec and "class Solution" in code:
            code = q["driver"]["py"]["pre"] + code + q["driver"]["py"]["post"]
        res = judge.judge("py", code, [t["in"] for t in q["samples"] + hidden], PY_LIMIT)
        if "compile_error" in res:
            notes.append("wrong solution (%s) doesn't run: %s" % (w.get("why", "?"), res["compile_error"][-200:])); status = "fail"; continue
        tests = q["samples"] + hidden
        caught = [i for i, (t, r) in enumerate(zip(tests, res["results"])) if r["tle"] or r["err"] or _norm(r["out"]) != _norm(t["out"])]
        if caught:
            how = "too slow" if any(res["results"][i]["tle"] for i in caught) else "wrong answer"
            notes.append("caught: %s (%s on %d test%s)" % (w.get("why", "wrong solution"), how, len(caught), "" if len(caught) == 1 else "s"))
        else:
            notes.append("NOT caught: %s passes every test. Add a test it fails." % w.get("why", "a wrong solution")); status = "fail"
    return status, "\n".join(notes)


def _dupes(company, q, check_dupes):
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, company, "questions"))
        p = os.path.join(d, company, "questions", q["id"] + ".json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(q, f)
        a = check_dupes.load(p)
    import glob
    paths = sorted(glob.glob(os.path.join(data.DATA_DIR, "*", "questions", "*.json")))
    bank = [check_dupes.load(x) for x in paths]
    companies = sorted({b["_key"].split("/")[0] for b in bank})
    found = []
    for b in bank:
        if b["_key"] == a["_key"]:
            continue
        level, j, why = check_dupes.compare(a, b)
        if level:
            found.append((level, j, b, why, check_dupes.settled(a, b)))
    where = "checked against %d questions from %s on this computer" % (len(bank), ", ".join(companies) or "no company")
    dup = [f for f in found if f[0] == "duplicate" and not f[4]]
    lines = ["%s %s %r (overlap %.2f%s)" % (lv, b["_key"], b.get("title", ""), j, ", " + ", ".join(w) if w else "")
             for lv, j, b, w, ok in sorted(found, key=lambda f: -f[1]) if not ok]
    if dup:
        return "fail", "\n".join(lines) + '\nThe same question? Add "alsoSeen": ["company/id"] instead of a copy. ' \
            'A different problem? Add "distinctFrom": ["company/id"].\n' + where
    if lines:
        return "warn", "\n".join(lines) + "\nLook at these; if one is the same question add \"alsoSeen\", otherwise \"distinctFrom\".\n" + where
    return "ok", where


def new_company_config(company, name, tagline=""):
    name = (name or company.title()).strip()
    return {
        "key": company, "name": name if name.lower().endswith("oa mock") else name + " OA Mock",
        "tagline": tagline or "Coding questions", "headline": "Sit a timed %s OA, then see what passed." % name,
        "blurb": "questions reported from %s OAs" % name, "defaultFmt": "oa", "custom": [],
        "formats": {
            "oa": {"name": "OA", "desc": "Easy, Medium and Hard coding questions · 90 min", "mins": 90, "pools": ["Easy", "Medium", "Hard"]},
            "custom": {"name": "Custom", "desc": "Pick the questions and the time", "mins": 60, "pools": []},
        },
        "offlist": [], "order": [],
    }


def save(company, q, name=None, tagline=None, replace=False):
    """Writes the question (after check() passed) and, for a new company, its company.json. Returns the paths."""
    res = check(company, q, replace=replace)
    if not res["ok"]:
        raise Problem("the question doesn't pass the checks yet")
    q = res["question"]
    d = os.path.join(data.DATA_DIR, company)
    written = []
    os.makedirs(os.path.join(d, "questions"), exist_ok=True)
    cfg = os.path.join(d, "company.json")
    if not os.path.exists(cfg):
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump(new_company_config(company, name, tagline), f, indent=2, ensure_ascii=False); f.write("\n")
        written.append(cfg)
    path = os.path.join(d, "questions", q["id"] + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(q, f, indent=1, ensure_ascii=False)
    written.append(path)
    _, _, _, _, build_catalog = _tools()
    cat = build_catalog.build()
    with open(build_catalog.OUT, "w", encoding="utf-8") as f:
        f.write(json.dumps(cat, indent=1, ensure_ascii=False) + "\n")
    written.append(build_catalog.OUT)
    return [os.path.relpath(p, data.ROOT).replace(os.sep, "/") for p in written]


# ------------------------------------------------------------------ pull requests

def _run(args, timeout=120, env=None, inp=None):
    r = subprocess.run(args, cwd=data.ROOT, input=inp, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                       env=dict(os.environ, GIT_TERMINAL_PROMPT="0", **(env or {})))
    return r.returncode, r.stdout.decode("utf-8", "replace").strip(), r.stderr.decode("utf-8", "replace").strip()


def upstream():
    """owner/repo of the origin remote on GitHub (where pull requests go)."""
    rc, url, _ = _run(["git", "remote", "get-url", "origin"], 10)
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", url) if rc == 0 else None
    return "%s/%s" % (m.group(1), m.group(2)) if m else None


def share_status():
    """What sending a pull request from here needs, and whether it's there."""
    st = library.git_state()
    out = {"git": st.get("git"), "upstream": upstream() if st.get("git") else None, "gh": False, "login": None}
    try:
        rc, _, _ = _run(["gh", "--version"], 10)
        out["gh"] = rc == 0
    except OSError:
        pass
    if out["gh"]:
        rc, login, _ = _run(["gh", "api", "user", "-q", ".login"], 20)
        out["login"] = login if rc == 0 and login else None
    return out


def share(company, qid, note=""):
    """Opens a pull request with data/<company>/questions/<qid>.json (+ company.json if the company is new)."""
    if not (data.KEY_RE.match(company or "") and ID_RE.match(qid or "")):
        raise Problem("bad company or question id")
    qpath = "data/%s/questions/%s.json" % (company, qid)
    if not os.path.isfile(os.path.join(data.ROOT, qpath)):
        raise Problem("save the question first")
    st = share_status()
    if not st["git"] or not st["upstream"]:
        raise Problem("this copy isn't a git clone of the GitHub repository")
    if not st["gh"]:
        raise Problem("the GitHub CLI (gh) isn't installed")
    if not st["login"]:
        raise Problem("the GitHub CLI isn't signed in: run  gh auth login  in a terminal, then try again")
    login, up = st["login"], st["upstream"]
    with open(os.path.join(data.ROOT, qpath), encoding="utf-8") as f:
        q = json.load(f)
    res = check(company, q, replace=True)
    if not res["ok"]:
        raise Problem("the question doesn't pass the checks: fix it and save again")
    log = []
    def git(*args, **kw):
        rc, out, err = _run(["git"] + list(args), **kw)
        log.append("$ git " + " ".join(args) + ("\n" + (out or err)[-500:] if (out or err) else ""))
        if rc:
            raise Problem("git %s failed: %s" % (args[0], (err or out).splitlines()[-1] if (err or out) else rc))
        return out
    git("fetch", "--quiet", "origin", timeout=300)
    base = "origin/main"
    files = {qpath: open(os.path.join(data.ROOT, qpath), "rb").read()}
    cfg = "data/%s/company.json" % company
    new_company = subprocess.run(["git", "cat-file", "-e", "%s:%s" % (base, cfg)], cwd=data.ROOT,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0
    if new_company:
        files[cfg] = open(os.path.join(data.ROOT, cfg), "rb").read()
    # data/catalog.json is left out: GitHub rebuilds it after the merge (.github/workflows/catalog.yml)

    # a commit on top of GitHub's main with just these files, built in a temporary index (your files stay as they are)
    with tempfile.TemporaryDirectory() as tmp:
        env = {"GIT_INDEX_FILE": os.path.join(tmp, "index")}
        git("read-tree", base, env=env)
        for path, blob in files.items():
            sha = git("hash-object", "-w", "--stdin", inp=blob)
            git("update-index", "--add", "--cacheinfo", "100644,%s,%s" % (sha, path), env=env)
        tree = git("write-tree", env=env)
    name = _run(["git", "config", "user.name"], 10)[1] or login
    email = _run(["git", "config", "user.email"], 10)[1] or "%s@users.noreply.github.com" % login
    who = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email}
    title = "Add %s/%s: %s" % (company, qid, q.get("title", qid))
    commit = git("commit-tree", tree, "-p", base, "-m", title, env=who)

    branch = "add-%s-%s-%s" % (company, qid, time.strftime("%Y%m%d%H%M%S"))
    owner = up.split("/")[0]
    if login.lower() == owner.lower():
        target, head = up, branch
    else:
        rc, fork, err = _run(["gh", "api", "-X", "POST", "repos/%s/forks" % up, "-q", ".full_name"], 120)
        if rc or not fork:
            raise Problem("couldn't fork %s: %s" % (up, err[-300:]))
        log.append("fork: " + fork)
        target, head = fork, "%s:%s" % (fork.split("/")[0], branch)
    url = "https://github.com/%s.git" % target
    for attempt in range(6):          # a brand-new fork can take a few seconds to accept pushes
        rc, out, err = _run(["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
                             "push", url, "%s:refs/heads/%s" % (commit, branch)], 300)
        if rc == 0:
            break
        time.sleep(4)
    else:
        raise Problem("couldn't push to %s: %s" % (target, err.splitlines()[-1] if err else rc))
    log.append("pushed %s to %s" % (branch, target))
    summary = "\n".join("- %s: %s" % (c["name"], c["status"]) for c in res["checks"])
    src = ", ".join("%s: %s" % (k, q[k]) for k in ("src", "year", "month", "college", "role") if q.get(k))
    body = ("Adds **%s** to %s%s.\n\n%s\n\nSource: %s\n\nLocal checks:\n%s\n\n_Sent from the OA Mock app._"
            % (q.get("title", qid), company, " (new company)" if new_company else "", note.strip(), src or "not given", summary))
    rc, pr, err = _run(["gh", "pr", "create", "--repo", up, "--base", "main", "--head", head, "--title", title, "--body", body], 120)
    if rc:
        raise Problem("pushed the branch, but couldn't open the pull request: %s" % (err.splitlines()[-1] if err else rc))
    return {"url": pr.splitlines()[-1], "branch": branch, "log": "\n".join(log)}
