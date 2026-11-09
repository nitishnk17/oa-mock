"""Past submissions, kept on disk so you can look back at them (and grep them).

.oa-cache/submissions/<company>/<question>/<when>_<lang>_<score>.<ext>    your code, as you submitted it
.oa-cache/submissions/<company>/<question>/<when>_<lang>_<score>.json     score, tests passed, test format, ...

The folder is git-ignored. Set OA_CACHE to keep it somewhere else.
"""
import json, os, re, threading, time

from . import data

CACHE_DIR = os.path.abspath(os.environ.get("OA_CACHE") or os.path.join(data.ROOT, ".oa-cache"))
SUB_DIR = os.path.join(CACHE_DIR, "submissions")
EXT = {"py": "py", "cpp": "cpp", "java": "java", "js": "js", "sql": "sql"}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,80}$")
MAX_CODE = 512 * 1024
_lock = threading.Lock()


class BadRequest(ValueError):
    pass


def _qdir(company, qid):
    if not data.KEY_RE.match(company or "") or not ID_RE.match(qid or ""):
        raise BadRequest("bad company or question id")
    return os.path.join(SUB_DIR, company, qid)


def save(req):
    """Store one submission. Returns its metadata."""
    company, qid, lang = req.get("company"), req.get("qid"), req.get("lang")
    code = req.get("code")
    if lang not in EXT:
        raise BadRequest("bad language")
    if not isinstance(code, str) or len(code) > MAX_CODE:
        raise BadRequest("code missing or too large")
    d = _qdir(company, qid)
    try:
        score = max(0, min(100, int(req.get("score", 0))))
    except (TypeError, ValueError):
        score = 0
    with _lock:
        os.makedirs(d, exist_ok=True)
        now = time.time()
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(now)) + "-%03d" % int(now * 1000 % 1000)
        sid = "%s_%s_%03d" % (stamp, lang, score)
        while os.path.exists(os.path.join(d, sid + ".json")):
            sid += "x"
        meta = {
            "id": sid, "company": company, "qid": qid, "title": str(req.get("title", qid))[:200],
            "lang": lang, "score": score, "passed": int(req.get("passed", 0) or 0), "total": int(req.get("total", 0) or 0),
            "mode": "practice" if req.get("practice") else "test", "format": str(req.get("format", ""))[:60],
            "style": "hackerrank" if req.get("style") == "hackerrank" else "leetcode",
            "at": int(now * 1000), "file": "%s.%s" % (sid, EXT[lang]),
        }
        with open(os.path.join(d, meta["file"]), "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        with open(os.path.join(d, sid + ".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=1)
    meta["path"] = os.path.join(d, meta["file"])
    return meta


def listing(company, qid=None, limit=200):
    """Newest first. Without qid, all questions of the company."""
    if not data.KEY_RE.match(company or ""):
        raise BadRequest("bad company")
    base = os.path.join(SUB_DIR, company)
    if not os.path.isdir(base):
        return []
    qids = [qid] if qid else sorted(os.listdir(base))
    out = []
    for q in qids:
        d = _qdir(company, q)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.endswith(".json"):
                try:
                    with open(os.path.join(d, name), encoding="utf-8") as f:
                        out.append(json.load(f))
                except (OSError, ValueError):
                    pass
    out.sort(key=lambda m: m.get("at", 0), reverse=True)
    return out[:max(1, min(int(limit), 1000))]


def read(company, qid, sid):
    """{"meta": ..., "code": ...} or None."""
    d = _qdir(company, qid)
    if not ID_RE.match(sid or ""):
        raise BadRequest("bad id")
    mp = os.path.join(d, sid + ".json")
    if not os.path.isfile(mp):
        return None
    with open(mp, encoding="utf-8") as f:
        meta = json.load(f)
    cp = os.path.join(d, os.path.basename(meta.get("file", "")))
    if not os.path.isfile(cp):
        return None
    with open(cp, encoding="utf-8") as f:
        code = f.read()
    meta["path"] = cp
    return {"meta": meta, "code": code}


def delete(company, qid, sid):
    d = _qdir(company, qid)
    if not ID_RE.match(sid or ""):
        raise BadRequest("bad id")
    gone = False
    with _lock:
        mp = os.path.join(d, sid + ".json")
        if os.path.isfile(mp):
            with open(mp, encoding="utf-8") as f:
                meta = json.load(f)
            cp = os.path.join(d, os.path.basename(meta.get("file", "")))
            for p in (cp, mp):
                if os.path.isfile(p):
                    os.remove(p); gone = True
    return gone
