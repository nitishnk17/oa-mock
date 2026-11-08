#!/usr/bin/env python3
"""Checks the colour contrast of web/static/css/tokens.css, in light and dark (WCAG 2 ratios).

    python3 tools/check_contrast.py

Text pairs need 4.5:1; line numbers, placeholders and comments inside a selection 3:1. Exit code 1 if a pair falls short.
"""
import os, re, sys

CSS = os.path.join(os.path.dirname(__file__), "..", "web", "static", "css", "tokens.css")
TEXT, UI = 4.5, 3.0


def blocks(css):
    """{selector: {var: value}} for the blocks that set colour tokens."""
    out = {}
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*--[^{}]*)\}", css):
        vars_ = dict(re.findall(r"--([\w-]+)\s*:\s*(#[0-9A-Fa-f]{6})", body))
        if vars_:
            for s in sel.split(","):
                out.setdefault(s.strip().split("\n")[-1].strip(), {}).update(vars_)
    return out


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    a, b = lum(a), lum(b)
    return (max(a, b) + .05) / (min(a, b) + .05)


SURFACES = ["bg", "bg-2", "surface", "surface-2"]
PAIRS = (
    [(t, s, TEXT) for t in ("text", "text-2") for s in SURFACES]
    + [("accent", s, TEXT) for s in SURFACES + ["accent-soft"]] + [("on-accent", "accent", TEXT), ("on-accent", "accent-hover", TEXT)]
    + [(c + "-ink", s, TEXT) for c in ("slate", "amber", "red", "success") for s in SURFACES + [c + "-soft"]]
    + [("text-3", s, UI) for s in ("surface", "surface-2")]
)
CODE = [(t, s, TEXT) for t in ("code-ink", "sx-kw", "sx-fn", "sx-str", "sx-num", "sx-com", "sx-type", "sx-op") for s in ("code-bg", "code-line")] \
    + [(t, "code-sel", TEXT if t != "sx-com" else UI) for t in ("code-ink", "sx-kw", "sx-fn", "sx-str", "sx-num", "sx-com", "sx-type", "sx-op")] \
    + [("code-num-ln", "code-gutter", UI)]


def main():
    b = blocks(open(CSS, encoding="utf-8").read())
    light = b[":root"]
    themes = {
        "light": light,
        "dark": dict(light, **b[':root[data-theme="dark"]']),
        "editor light": dict(light, **b[".ed-light"]),
        "editor dark": dict(light, **b[".ed-dark"]),
    }
    bad = 0
    for name, t in themes.items():
        pairs = CODE if name.startswith("editor") else PAIRS + CODE
        worst = min((ratio(t[a], t[s]), a, s, need) for a, s, need in pairs)
        fails = [(a, s, ratio(t[a], t[s]), need) for a, s, need in pairs if ratio(t[a], t[s]) < need]
        for a, s, r, need in fails:
            print("FAIL %-12s %-12s on %-12s %.2f (needs %.1f)" % (name, a, s, r, need))
        bad += len(fails)
        print("%-12s %d pairs, lowest %.2f (%s on %s)" % (name, len(pairs), worst[0], worst[1], worst[2]))
    print("all pairs pass" if not bad else "%d pair(s) below the minimum" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
