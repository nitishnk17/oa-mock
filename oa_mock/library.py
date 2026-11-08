"""Which companies are on this computer, and downloading / updating / removing them with git.

A slim clone (git clone --filter=blob:none --sparse) has the app but only the companies you pick:
  download  git sparse-checkout add data/<company>      (fetches just that company's files)
  update    git pull --ff-only                          (the app + the companies you have)
  remove    git sparse-checkout set <everything else>   (refused if you changed files there)
  check     git fetch                                   (find new questions / app updates)
A full clone has every company already; removing one turns it into a slim clone.
Without git (e.g. a ZIP download) the page only lists what's in data/.

Jobs run one at a time in a background thread; the page polls job() for progress. Only fixed git
commands run, with a company name checked against the catalog, so the page can't run anything else.
"""
import json, os, subprocess, threading, time

from . import data

ROOT = data.ROOT
BRANCH = "origin/main"
_job = {"id": 0, "state": "idle"}
_lock = threading.Lock()
KEY_RE = data.KEY_RE


def _git(*args, timeout=60, check=False):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="echo", LC_ALL="C")
    r = subprocess.run(["git", "-C", ROOT] + list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, env=env)
    out = r.stdout.decode("utf-8", "replace")
    if check and r.returncode:
        raise RuntimeError(out.strip() or "git %s failed" % args[0])
    return r.returncode, out


def git_state():
    """{git, sparse, remote, behind} about this copy of the app."""
    try:
        rc, out = _git("rev-parse", "--is-inside-work-tree", timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return {"git": False, "why": "git isn't installed"}
    top = _git("rev-parse", "--show-toplevel", timeout=10)[1].strip() if rc == 0 else ""
    if rc or out.strip() != "true" or os.path.realpath(top) != os.path.realpath(ROOT):
        return {"git": False, "why": "this copy wasn't cloned with git (e.g. a ZIP download)"}
    st = {"git": True}
    st["sparse"] = _git("config", "--get", "core.sparseCheckout", timeout=10)[1].strip() == "true"
    st["remote"] = _git("rev-parse", "--verify", "-q", BRANCH, timeout=10)[0] == 0
    st["behind"] = int(_git("rev-list", "--count", "HEAD.." + BRANCH, timeout=10)[1].strip() or 0) if st["remote"] else 0
    # data/catalog.json is generated (saving a question rewrites it), so it doesn't count
    st["dirty"] = any(l[3:].strip() != "data/catalog.json"
                      for l in _git("status", "--porcelain", "--untracked-files=no", timeout=20)[1].splitlines() if l.strip())
    return st


def _catalog(ref=None):
    """Catalog from the working copy, or from a git ref (origin/main) for companies not downloaded."""
    if ref:
        rc, out = _git("show", "%s:data/catalog.json" % ref, timeout=60)
        if rc == 0:
            try: return json.loads(out)
            except ValueError: pass
        return None
    p = os.path.join(data.DATA_DIR, "catalog.json")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def _trees(ref):
    """{company: tree id} under data/ at a ref; a company whose tree id changed has new or edited questions."""
    rc, out = _git("ls-tree", "-d", ref, "data/", timeout=20)
    trees = {}
    for line in out.splitlines() if rc == 0 else []:
        meta, _, path = line.partition("\t")
        if meta.split()[1:2] == ["tree"]:
            trees[path.rsplit("/", 1)[-1]] = meta.split()[2]
    return trees


def _tree(ref, key):
    return _trees(ref).get(key)


def listing():
    st = git_state()
    installed = {k: (n, t) for k, n, t in data.companies()}
    remote_cat = _catalog(BRANCH) if st.get("remote") else None
    by_key = {}
    for c in (remote_cat or {}).get("companies", []):      # what's on GitHub (as of the last check)
        by_key[c["key"]] = dict(c)
    for c in (_catalog() or {}).get("companies", []):       # this copy's catalog wins for what you have
        if c["key"] in installed or c["key"] not in by_key:
            by_key[c["key"]] = dict(c)
    for k, (name, tagline) in installed.items():            # downloaded but not in any catalog yet
        by_key.setdefault(k, {"key": k})
        by_key[k].update(name=name, tagline=tagline)
    head_trees = _trees("HEAD") if st.get("git") else {}
    remote_trees = _trees(BRANCH) if st.get("remote") else {}
    out = []
    for k, c in by_key.items():
        c["installed"] = k in installed
        c["update"] = bool(c["installed"] and k in head_trees and k in remote_trees and head_trees[k] != remote_trees[k])
        c["available"] = bool(not c["installed"] and (k in head_trees or k in remote_trees))
        c["onlyLocal"] = bool(c["installed"] and st.get("git") and k not in head_trees)
        if c["installed"] or c["available"]:
            out.append(c)
    out.sort(key=lambda c: (not c["installed"], c.get("name", c["key"]).lower()))
    return {"git": st, "companies": out, "job": job()}


def job():
    with _lock:
        return dict(_job)


def _platform_dirs():
    """Top-level folders of the app (everything but data/), for the sparse-checkout list."""
    rc, out = _git("ls-tree", "-d", "--name-only", "HEAD", timeout=20)
    return [d for d in out.split() if d and d != "data"]


def _installed_keys():
    return sorted(k for k, _, _ in data.companies())


def _cone(keys):
    """sparse-checkout set: the whole app (worked out when the step runs, so new app folders come along) + these companies."""
    return lambda: ["sparse-checkout", "set", "--cone"] + _platform_dirs() + ["data/" + k for k in sorted(set(keys))]


def _tidy():
    """Before pulling: drop local changes to the generated catalog, and your own copies of question files that are
    now on GitHub byte for byte (e.g. a question you sent as a pull request that got merged); git would refuse
    to overwrite them otherwise."""
    done = []
    if _git("diff", "--quiet", "--", "data/catalog.json", timeout=20)[0]:
        _git("checkout", "--", "data/catalog.json", timeout=20); done.append("reset data/catalog.json (it's regenerated)")
    rc, out = _git("ls-files", "--others", "--exclude-standard", "--", "data", timeout=30)
    for path in out.splitlines() if rc == 0 else []:
        rc1, theirs = _git("rev-parse", "-q", "--verify", "%s:%s" % (BRANCH, path), timeout=10)
        if rc1 or not theirs.strip():
            continue
        mine = _git("hash-object", path, timeout=10)[1].strip()
        if mine == theirs.strip():
            os.remove(os.path.join(ROOT, path)); done.append("%s is now on GitHub" % path)
    return "\n".join(done)
_tidy.python = True


def _run_job(steps):
    log = []
    def say(line):
        with _lock:
            log.append(line); _job["log"] = "\n".join(log)[-8000:]
    try:
        for desc, args, timeout in steps:
            with _lock: _job["step"] = desc
            if getattr(args, "python", False):
                note = args()
                if note: say(note)
                continue
            args = args() if callable(args) else args
            say("$ git " + " ".join(args))
            rc, out = _git(*args, timeout=timeout)
            if out.strip(): say(out.strip()[-3000:])
            if rc:
                last = [l for l in out.strip().splitlines() if l.strip()]
                raise RuntimeError(last[-1] if last else "git %s failed" % args[0])
        with _lock:
            _job.update(state="done", finished=time.time())
    except Exception as e:
        with _lock:
            _job.update(state="failed", error=str(e), finished=time.time())


def start(kind, key=None):
    """kind: check | download | update | remove. Returns the job, or raises ValueError with a reason."""
    st = git_state()
    if not st.get("git"):
        raise ValueError("Downloading companies needs a git clone: " + st.get("why", ""))
    if kind in ("download", "remove") and (not key or not KEY_RE.match(key)):
        raise ValueError("bad company")
    installed = _installed_keys()
    in_head = key in _trees("HEAD") if key else False
    pull = ("update", ["pull", "--ff-only", "--quiet"], 600)
    tidy = ("tidy", _tidy, 0)
    if kind == "download":
        if key in installed: raise ValueError("already downloaded")
        if not in_head and key not in _trees(BRANCH): raise ValueError("no such company in the repository")
        if not in_head and st.get("dirty"):
            raise ValueError("%s needs an app update first, and you have uncommitted changes to files from the repository; commit or stash them" % key)
        steps = [] if in_head else [tidy, pull]            # new on GitHub: bring this copy up to date first
        if st["sparse"] or in_head:                         # (a full clone has it after the pull)
            steps.append(("download", _cone(installed + [key]), 900))
    elif kind == "remove":
        if key not in installed: raise ValueError("not downloaded")
        if not in_head: raise ValueError("data/%s isn't from the repository (your own questions?); delete the folder yourself if you mean to" % key)
        if _git("status", "--porcelain", "--", "data/" + key, timeout=20)[1].strip():
            raise ValueError("you have changes in data/%s (new or edited questions?). Commit or move them first." % key)
        steps = [("remove", _cone([k for k in installed if k != key]), 120)]
    elif kind == "update":
        if st.get("dirty"): raise ValueError("you have uncommitted changes to files from the repository; commit or stash them first")
        steps = [tidy, pull]
        if st["sparse"]:
            steps.append(("refresh", _cone(installed), 900))
    elif kind == "check":
        steps = [("check", ["fetch", "--quiet", "origin"], 120)]
    else:
        raise ValueError("unknown action")
    with _lock:
        if _job.get("state") == "running":
            raise ValueError("another download or update is still running")
        _job.clear(); _job.update(id=int(time.time() * 1000), kind=kind, company=key, state="running", log="", started=time.time())
        snapshot = dict(_job)
    threading.Thread(target=_run_job, args=(steps,), daemon=True).start()
    return snapshot
