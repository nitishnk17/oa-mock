#!/usr/bin/env python3
"""One-off: adds year / month / college / role to existing questions, taken only from what each
question's `src` (and its source notes) say. Unknown stays null; the app shows "Year not recorded".

    python3 tools/meta_backfill.py
"""
import json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
A, F, J, M = "amazon", "flipkart", "juspay", "mathworks"

# (year, month, college, role); month 1-12 or None
META = {
    (A, "flip"): (2026, None, None, "SDE Intern"), (A, "watchlist"): (2026, None, None, "SDE Intern"), (A, "sjt"): (2026, None, None, "SDE Intern"),
    (A, "evenrun"): (2026, 7, "IIIT Delhi", "Intern"), (A, "palsub"): (2026, 7, "IIIT Delhi", "Intern"),
    **{(A, q): (2024, None, None, "SDE") for q in ("findpairs", "parcels", "outlier", "winners", "qmarks")},
    (F, "ads"): (None, None, None, "SDE"), (F, "bignum"): (None, None, None, "SDE"), (F, "robots"): (None, None, None, "SDE"),
    (F, "bags"): (None, None, None, "Data Engineer"), (F, "houses"): (None, None, None, "Data Engineer"),
    (F, "island"): (None, None, "IIT BHU", "Data Engineer"), (F, "poscode"): (None, None, "IIT BHU", "Data Engineer"),
    (F, "sayclap"): (None, None, "IIT BHU", "Data Engineer"), (F, "sql"): (None, None, "IIT BHU", "Data Engineer"),
    (F, "cascade"): (None, None, "IIT Bombay", "UI Engineer"), (F, "colour"): (None, None, "IIT Bombay", "UI Engineer"),
    (F, "indeg"): (None, None, None, None), (F, "racing"): (None, None, None, None), (F, "snake"): (None, None, None, None),
    (J, "calc"): (2026, 2, None, "SDE Intern"), (J, "openlock"): (2026, 3, None, "SDE-1"),
    (J, "inversions"): (2025, 8, None, "SDE-1"), (J, "puddles"): (2025, 8, None, "SDE-1"),
    (J, "leader"): (2025, 3, None, None), (J, "workers"): (2025, 3, None, None),
    **{(J, q): (None, None, None, None) for q in ("cyclesum", "maxweight", "meeting", "fastest", "reach", "cycling", "equalize",
                                                  "factory", "hiker", "magical", "parking", "rebels", "treelock", "vineyard")},
    (M, "minids"): (2026, None, "IIT Bombay", "Embedded Systems"), (M, "twodenom"): (2026, None, "IIT Bombay", "Embedded Systems"),
    (M, "majparts"): (2026, None, "IIT Bombay", "Software Engineer"), (M, "palsubs"): (2026, None, "IIT Bombay", "Software Engineer"),
    (M, "beauty"): (2026, None, "IIT Bombay", "Software Engineer"),
}

if __name__ == "__main__":
    for (company, qid), (year, month, college, role) in sorted(META.items()):
        p = os.path.join(ROOT, "data", company, "questions", qid + ".json")
        with open(p, encoding="utf-8") as f:
            q = json.load(f)
        for k, v in (("year", year), ("month", month), ("college", college), ("role", role)):
            if v is None: q.pop(k, None)
            else: q[k] = v
        with open(p, "w", encoding="utf-8") as f:
            json.dump(q, f, indent=1, ensure_ascii=False)
    print("updated", len(META), "questions")
