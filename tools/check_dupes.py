#!/usr/bin/env python3
"""Finds questions that may already be in the bank, across every company.

    python3 tools/check_dupes.py                  # every pair in the bank
    python3 tools/check_dupes.py amazon           # questions of one company against everything
    python3 tools/check_dupes.py path/to/new.json # a question you're writing, against everything
    add --deep to also run each Python reference on the other question's samples (catches the same problem
    worded differently; slower, and it runs the references)

Signals, strongest first:
  same samples        an identical sample input + output pair            -> duplicate
  statement           word-trigram overlap of the normalised statements  -> >= 0.45 duplicate, >= 0.25 similar
  same title          identical normalised titles                        -> similar
  same pattern link   the same LeetCode "practise the pattern" link      -> shown as extra evidence only

A pair is settled when either question lists the other, as "company/id", in
  alsoSeen      the same question, also reported at another company or in another year
  distinctFrom  checked: looks alike but is a different problem
Exit code 1 when an unsettled duplicate is found (similar pairs are only reported).
"""
import glob, html, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DUP, SIMILAR = 0.45, 0.25
STOP = set("a an the of to in is are be for and or on with by as at it its this that these those you your each every from than "
           "which what when where who how can will given print return output input one two first second line lines contains".split())


def words(text):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or "")).lower()
    text = re.sub(r"\d+", "#", text)
    return [w for w in re.findall(r"[a-z#]+", text) if w not in STOP]


def shingles(ws, k=3):
    return {tuple(ws[i:i + k]) for i in range(len(ws) - k + 1)} or {tuple(ws)}


def load(path):
    with open(path, encoding="utf-8") as f:
        q = json.load(f)
    company = os.path.basename(os.path.dirname(os.path.dirname(path)))
    q["_key"] = "%s/%s" % (company, q.get("id", os.path.basename(path)[:-5]))
    q["_sh"] = shingles(words(q.get("body", "")))
    q["_title"] = " ".join(words(q.get("title", "")))
    q["_samples"] = {(s.get("in", "").strip(), str(s.get("out", "")).strip()) for s in q.get("samples", []) if "in" in s}
    return q


def compare(a, b):
    j = len(a["_sh"] & b["_sh"]) / max(1, len(a["_sh"] | b["_sh"]))
    why = []
    if a["_samples"] & b["_samples"]: why.append("same sample")
    if a["_title"] and a["_title"] == b["_title"]: why.append("same title")
    if a.get("lcurl") and a.get("lcurl") == b.get("lcurl"): why.append("same pattern link")
    level = "duplicate" if "same sample" in why or j >= DUP else "similar" if j >= SIMILAR or "same title" in why else None
    return level, j, why


def same_behaviour(a, b):
    """Does a's Python reference reproduce b's tests (samples + up to 8 small hidden)? Runs a's reference.
    Returns "duplicate", "similar" (only one case to compare) or False."""
    sys.path.insert(0, os.path.join(ROOT, "app"))
    from server import judge
    if not a.get("ref") or a.get("type", "code") != "code" or not b["_samples"]:
        return False
    d = (a.get("driver") or {}).get("py")
    src = d["pre"] + a["ref"] + d["post"] if d else a["ref"]
    cases = sorted(b["_samples"]) + [(t["in"].strip(), str(t["out"]).strip()) for t in b.get("hidden", []) if "in" in t and len(t["in"]) < 20000]
    cases = cases[:8]
    res = judge.judge("py", src, [i + "\n" for i, _ in cases], 5000)
    if "compile_error" in res:
        return False
    if not all(not r["err"] and not r["tle"] and r["out"].split() == o.split() for r, (_, o) in zip(res["results"], cases)):
        return False
    return "duplicate" if len(cases) >= 2 else "similar"   # one matching case can be a coincidence


def settled(a, b):
    for x, y in ((a, b), (b, a)):
        if y["_key"] in (x.get("alsoSeen") or []) + (x.get("distinctFrom") or []):
            return True
    return False


def main(args):
    deep = "--deep" in args
    args = [x for x in args if x != "--deep"]
    bank = [load(p) for p in sorted(glob.glob(os.path.join(ROOT, "data", "*", "questions", "*.json")))]
    if not args:
        subjects = bank
    elif args[0].endswith(".json"):
        subjects = [load(os.path.abspath(args[0]))]
    else:
        subjects = [q for q in bank if q["_key"].split("/")[0] in args]
    seen, found = set(), []
    for a in subjects:
        for b in bank:
            if a["_key"] == b["_key"] or (b["_key"], a["_key"]) in seen:
                continue
            seen.add((a["_key"], b["_key"]))
            level, j, why = compare(a, b)
            if deep and level != "duplicate":
                hit = same_behaviour(a, b) or same_behaviour(b, a)
                if hit:
                    level = hit if level is None or hit == "duplicate" else level
                    why.append("a reference solves the other's tests" if hit == "duplicate" else "a reference solves the other's only sample")
            if level:
                found.append((level, j, a, b, why, settled(a, b)))
    found.sort(key=lambda x: (x[0] != "duplicate", -x[1]))
    unsettled = 0
    for level, j, a, b, why, ok in found:
        mark = "settled " if ok else ""
        unsettled += level == "duplicate" and not ok
        print("%-9s %s%-22s %-22s statement overlap %.2f%s" % (level.upper(), mark, a["_key"], b["_key"], j, ("  · " + ", ".join(why)) if why else ""))
        print("          %s  |  %s" % (a.get("title", ""), b.get("title", "")))
    print("\n%d question(s) checked against %d. %s" % (len(subjects), len(bank),
          "No likely duplicates." if not found else "%d unsettled duplicate(s), %d unsettled similar pair(s) to look at, %d settled." % (
              unsettled, sum(1 for f in found if not f[5] and f[0] != "duplicate"), sum(1 for f in found if f[5]))))
    if found:
        print('Same question? Add "alsoSeen": ["company/id"]. Different problem? Add "distinctFrom": ["company/id"].')
    return 1 if unsettled else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
