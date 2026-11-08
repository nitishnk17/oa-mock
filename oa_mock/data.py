"""Loads company configs and questions from data/<company>/.

data/<company>/company.json      name, formats, question order, ...
data/<company>/questions/<id>.json   one question each

Files are re-read when they change, so edits show up on the next page load.
"""
import json, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data")
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

_cache = {}   # key -> (signature, payload)


def _signature(key):
    """mtimes of every file of a company, to know when to reload."""
    d = os.path.join(DATA_DIR, key)
    files = [os.path.join(d, "company.json")] + sorted(
        os.path.join(d, "questions", f) for f in os.listdir(os.path.join(d, "questions")) if f.endswith(".json"))
    return tuple((f, os.path.getmtime(f)) for f in files)


def companies():
    """[(key, name, blurb)] for every folder in data/ with a company.json, sorted by name."""
    out = []
    for key in sorted(os.listdir(DATA_DIR)) if os.path.isdir(DATA_DIR) else []:
        p = os.path.join(DATA_DIR, key, "company.json")
        if KEY_RE.match(key) and os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                c = json.load(f)
            out.append((key, c.get("name", key), c.get("tagline", "")))
    return sorted(out, key=lambda c: c[1].lower())


def load(key):
    """{"config": ..., "questions": [...]} for one company, or None if it doesn't exist."""
    if not KEY_RE.match(key) or not os.path.isfile(os.path.join(DATA_DIR, key, "company.json")):
        return None
    sig = _signature(key)
    hit = _cache.get(key)
    if hit and hit[0] == sig:
        return hit[1]
    d = os.path.join(DATA_DIR, key)
    with open(os.path.join(d, "company.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    order = cfg.pop("order", None)
    if order is None:
        order = sorted(f[:-5] for f in os.listdir(os.path.join(d, "questions")) if f.endswith(".json"))
    questions = []
    for qid in order:
        with open(os.path.join(d, "questions", qid + ".json"), encoding="utf-8") as f:
            questions.append(json.load(f))
    payload = {"config": cfg, "questions": questions}
    _cache[key] = (sig, payload)
    return payload


def question(key, qid):
    """One question with all its tests (the server grades with these), or None."""
    p = load(key)
    if p is None:
        return None
    for q in p["questions"]:
        if q.get("id") == qid:
            return q
    return None


def _light(q):
    """What the page gets: everything except the hidden tests, which stay on the server."""
    out = {k: v for k, v in q.items() if k != "hidden"}
    out["hiddenCount"] = len(q.get("hidden", []))
    return out


_script_cache = {}


def as_script(key):
    """The company payload as a JS file that sets window.OA_DATA (without hidden tests)."""
    p = load(key)
    if p is None:
        return None
    sig = _cache[key][0]
    hit = _script_cache.get(key)
    if hit and hit[0] == sig:
        return hit[1]
    light = {"config": p["config"], "questions": [_light(q) for q in p["questions"]]}
    js = "window.OA_DATA = " + json.dumps(light, ensure_ascii=False).replace("</", "<\\/") + ";\n"
    _script_cache[key] = (sig, js)
    return js
