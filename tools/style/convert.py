#!/usr/bin/env python3
"""Turns full-program questions into LeetCode-style ones (function stub + hidden I/O driver).

    python3 tools/style/convert.py            # rewrite every question listed in specs.py
    python3 tools/style/convert.py --check    # only report what would change

For each question in specs.py this writes, into data/<company>/questions/<id>.json:
  stub[lang]    what the editor shows: class Solution / function with an empty body that returns a default
  driver[lang]  {pre, post}: reads the input in the question's format, calls the function, prints the result
  ref           the function-style Python reference from specs.py
  refcppProgram true, because the existing C++ reference stays a full program (it still passes every test)
and adds a "Function to complete" section to the statement.
The same driver templates serve every question, so a template that is right for one question is right
for all of them (tools/style/selftest.py checks each template in all four languages).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from specs import SPECS  # noqa: E402

PRE = {
    "py": "from typing import *\nimport sys, math, collections, heapq, bisect, itertools, functools\nfrom collections import *\n",
    "cpp": "#include <bits/stdc++.h>\nusing namespace std;\n",
    "java": "import java.util.*;\nimport java.io.*;\n",
    "js": "",
}
SCALAR = {"int", "long", "str", "line", "bool"}

# ---------------------------------------------------------------- types per language
PY_T = {"int": "int", "long": "int", "str": "str", "line": "str", "bool": "bool", "int[]": "List[int]", "long[]": "List[int]",
        "str[]": "List[str]", "bool[]": "List[bool]", "int[][]": "List[List[int]]"}
CPP_T = {"int": "int", "long": "long long", "str": "string", "line": "string", "bool": "bool", "int[]": "vector<int>",
         "long[]": "vector<long long>", "str[]": "vector<string>", "bool[]": "vector<bool>", "int[][]": "vector<vector<int>>"}
JAVA_T = {"int": "int", "long": "long", "str": "String", "line": "String", "bool": "boolean", "int[]": "int[]", "long[]": "long[]",
          "str[]": "String[]", "bool[]": "boolean[]", "int[][]": "int[][]"}
JS_T = {"int": "number", "long": "number", "str": "string", "line": "string", "bool": "boolean", "int[]": "number[]",
        "long[]": "number[]", "str[]": "string[]", "bool[]": "boolean[]", "int[][]": "number[][]"}
DEFAULT = {  # value an untouched stub returns, so it compiles and prints something of the right shape
    "py": {"int": "0", "long": "0", "str": '""', "bool": "False", "arr": "[]"},
    "cpp": {"int": "0", "long": "0", "str": '""', "bool": "false", "arr": "{}"},
    "java": {"int": "0", "long": "0", "str": '""', "bool": "false", "int[]": "new int[0]", "long[]": "new long[0]", "str[]": "new String[0]",
             "bool[]": "new boolean[0]", "int[][]": "new int[0][]"},
    "js": {"int": "0", "long": "0", "str": '""', "bool": "false", "arr": "[]"},
}


def ret_base(ret):
    return ret.split("/")[0]


def params(spec):
    """[(name, type)] passed to the function, in call order."""
    out = []
    for item in spec["read"]:
        if item[0] == "rows":
            out += [(n, t + "[]") for n, t in item[2]]
        elif not item[0].startswith("_"):
            out.append((item[0], item[1]))
    if spec.get("order"):
        d = dict(out); out = [(n, d[n]) for n in spec["order"]]
    return out


def lenexpr(x):
    return "(%s)" % x if isinstance(x, str) else str(x)


def default(lang, ret):
    b = ret_base(ret)
    d = DEFAULT[lang]
    return d.get(b) or d["arr"]


# ---------------------------------------------------------------- Python
def py_stub(spec):
    ps = ", ".join("%s: %s" % (n, PY_T[t]) for n, t in params(spec))
    return "class Solution:\n    def %s(self%s) -> %s:\n        return %s\n" % (
        spec["fn"], ", " + ps if ps else "", PY_T[ret_base(spec["ret"])], default("py", spec["ret"]))


def py_post(spec):
    L = ['', '', 'if __name__ == "__main__":', '    _raw = sys.stdin.read(); _t = _raw.split(); _p = 0']
    for it in spec["read"]:
        if it[0] == "rows":
            cols = it[2]
            L.append("    " + "; ".join("%s = []" % n for n, _ in cols))
            L.append("    for _ in range(%s):" % lenexpr(it[1]))
            for j, (n, t) in enumerate(cols):
                L.append("        %s.append(%s)" % (n, "int(_t[_p + %d])" % j if t in ("int", "long") else "_t[_p + %d]" % j))
            L.append("        _p += %d" % len(cols))
            continue
        n, t = it[0], it[1]
        if t in ("int", "long"): L.append("    %s = int(_t[_p]); _p += 1" % n)
        elif t == "str": L.append("    %s = _t[_p]; _p += 1" % n)
        elif t == "line": L.append('    %s = _raw.rstrip("\\r\\n")' % n)
        elif t in ("int[]", "long[]"): L.append("    %s = list(map(int, _t[_p:_p + %s])); _p += %s" % (n, lenexpr(it[2]), lenexpr(it[2])))
        elif t == "str[]": L.append("    %s = _t[_p:_p + %s]; _p += %s" % (n, lenexpr(it[2]), lenexpr(it[2])))
        elif t == "int[][]":
            R, C = lenexpr(it[2]), lenexpr(it[3])
            L.append("    %s = [list(map(int, _t[_p + _i * %s:_p + (_i + 1) * %s])) for _i in range(%s)]; _p += %s * %s" % (n, C, C, R, R, C))
        else: raise ValueError(t)
    L.append("    _r = Solution().%s(%s)" % (spec["fn"], ", ".join(n for n, _ in params(spec))))
    r = spec["ret"]
    if r in ("int", "long", "str"): L.append("    print(_r)")
    elif r == "bool": L.append('    print("true" if _r else "false")')
    elif r == "bool[]/lines": L.append('    print("\\n".join("true" if _x else "false" for _x in _r))')
    elif r.endswith("/lines"): L.append('    print("\\n".join(map(str, _r)))')
    elif r == "int[][]": L.append('    print("\\n".join(" ".join(map(str, _row)) for _row in _r))')
    else: L.append('    print(" ".join(map(str, _r)))')
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- C++
def cpp_param(n, t):
    return ("%s& %s" if t.endswith("]") else "%s %s") % (CPP_T[t], n)


def cpp_stub(spec):
    ps = ", ".join(cpp_param(n, t) for n, t in params(spec))
    return "class Solution {\npublic:\n    %s %s(%s) {\n        \n        return %s;\n    }\n};\n" % (
        CPP_T[ret_base(spec["ret"])], spec["fn"], ps, default("cpp", spec["ret"]))


def cpp_post(spec):
    L = ["", "", "int main() {", "    ios::sync_with_stdio(false); cin.tie(nullptr);"]
    for it in spec["read"]:
        if it[0] == "rows":
            cols, n_ = it[2], lenexpr(it[1])
            for n, t in cols: L.append("    %s %s(%s);" % (CPP_T[t + "[]"], n, n_))
            L.append("    for (int _i = 0; _i < %s; _i++) cin%s;" % (n_, "".join(" >> %s[_i]" % n for n, _ in cols)))
            continue
        n, t = it[0], it[1]
        if t in ("int", "long", "str"): L.append("    %s %s; cin >> %s;" % (CPP_T[t], n, n))
        elif t == "line":
            L.append("    string %s((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>());" % n)
            L.append("    while (!%s.empty() && (%s.back() == '\\n' || %s.back() == '\\r')) %s.pop_back();" % (n, n, n, n))
        elif t in ("int[]", "long[]", "str[]"):
            L.append("    %s %s(%s); for (auto& _x : %s) cin >> _x;" % (CPP_T[t], n, lenexpr(it[2]), n))
        elif t == "int[][]":
            L.append("    vector<vector<int>> %s(%s, vector<int>(%s)); for (auto& _row : %s) for (auto& _x : _row) cin >> _x;" % (n, lenexpr(it[2]), lenexpr(it[3]), n))
        else: raise ValueError(t)
    L.append("    auto _r = Solution().%s(%s);" % (spec["fn"], ", ".join(n for n, _ in params(spec))))
    r = spec["ret"]
    if r in ("int", "long", "str"): L.append('    cout << _r << "\\n";')
    elif r == "bool": L.append('    cout << (_r ? "true" : "false") << "\\n";')
    elif r == "bool[]/lines": L.append('    for (bool _x : _r) cout << (_x ? "true" : "false") << "\\n";')
    elif r.endswith("/lines"): L.append('    for (auto& _x : _r) cout << _x << "\\n";')
    elif r == "int[][]": L.append('    for (auto& _row : _r) { for (size_t _i = 0; _i < _row.size(); _i++) { if (_i) cout << \' \'; cout << _row[_i]; } cout << "\\n"; }')
    else: L.append('    for (size_t _i = 0; _i < _r.size(); _i++) { if (_i) cout << \' \'; cout << _r[_i]; }\n    cout << "\\n";')
    L += ["    return 0;", "}"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- Java
J_PARSE = {"int": "Integer.parseInt(_t[_p++])", "long": "Long.parseLong(_t[_p++])", "str": "_t[_p++]"}


def java_stub(spec):
    ps = ", ".join("%s %s" % (JAVA_T[t], n) for n, t in params(spec))
    return "class Solution {\n    public %s %s(%s) {\n        \n        return %s;\n    }\n}\n" % (
        JAVA_T[ret_base(spec["ret"])], spec["fn"], ps, default("java", spec["ret"]))


def java_post(spec):
    L = ["", "", "public class Main {", "    public static void main(String[] args) throws IOException {",
         "        String _raw = new String(System.in.readAllBytes());",
         '        String[] _t = _raw.trim().isEmpty() ? new String[0] : _raw.trim().split("\\\\s+");',
         "        int _p = 0;"]
    for it in spec["read"]:
        if it[0] == "rows":
            cols, n_ = it[2], lenexpr(it[1])
            for n, t in cols: L.append("        %s %s = new %s[%s];" % (JAVA_T[t + "[]"], n, JAVA_T[t], n_))
            L.append("        for (int _i = 0; _i < %s; _i++) { %s }" % (n_, " ".join("%s[_i] = %s;" % (n, J_PARSE[t]) for n, t in cols)))
            continue
        n, t = it[0], it[1]
        if t in J_PARSE: L.append("        %s %s = %s;" % (JAVA_T[t], n, J_PARSE[t]))
        elif t == "line": L.append('        String %s = _raw.replaceAll("[\\\\r\\\\n]+$", "");' % n)
        elif t in ("int[]", "long[]", "str[]"):
            e = t[:-2]
            L.append("        %s %s = new %s[%s]; for (int _i = 0; _i < %s.length; _i++) %s[_i] = %s;" % (JAVA_T[t], n, JAVA_T[e], lenexpr(it[2]), n, n, J_PARSE[e]))
        elif t == "int[][]":
            L.append("        int[][] %s = new int[%s][%s]; for (int[] _row : %s) for (int _j = 0; _j < _row.length; _j++) _row[_j] = Integer.parseInt(_t[_p++]);" % (n, lenexpr(it[2]), lenexpr(it[3]), n))
        else: raise ValueError(t)
    rt = JAVA_T[ret_base(spec["ret"])]
    L.append("        %s _r = new Solution().%s(%s);" % (rt, spec["fn"], ", ".join(n for n, _ in params(spec))))
    L.append("        StringBuilder _sb = new StringBuilder();")
    r = spec["ret"]
    if r in ("int", "long", "str"): L.append("        _sb.append(_r).append('\\n');")
    elif r == "bool": L.append('        _sb.append(_r ? "true" : "false").append(\'\\n\');')
    elif r == "bool[]/lines": L.append('        for (boolean _x : _r) _sb.append(_x ? "true" : "false").append(\'\\n\');')
    elif r.endswith("/lines"): L.append("        for (int _i = 0; _i < _r.length; _i++) _sb.append(_r[_i]).append('\\n');")
    elif r == "int[][]": L.append("        for (int[] _row : _r) { for (int _i = 0; _i < _row.length; _i++) { if (_i > 0) _sb.append(' '); _sb.append(_row[_i]); } _sb.append('\\n'); }")
    else: L.append("        for (int _i = 0; _i < _r.length; _i++) { if (_i > 0) _sb.append(' '); _sb.append(_r[_i]); }\n        _sb.append('\\n');")
    L += ["        System.out.print(_sb);", "    }", "}"]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- JavaScript
def js_stub(spec):
    ps = params(spec)
    doc = "/**\n" + "".join(" * @param {%s} %s\n" % (JS_T[t], n) for n, t in ps) + " * @return {%s}\n */\n" % JS_T[ret_base(spec["ret"])]
    return doc + "var %s = function(%s) {\n    \n    return %s;\n};\n" % (spec["fn"], ", ".join(n for n, _ in ps), default("js", spec["ret"]))


def js_post(spec):
    L = ["", "", ";(() => {", '    const _raw = require("fs").readFileSync(0, "utf8");',
         "    const _t = _raw.split(/\\s+/).filter(Boolean); let _p = 0;"]
    for it in spec["read"]:
        if it[0] == "rows":
            cols, n_ = it[2], lenexpr(it[1])
            L.append("    const %s;" % ", ".join("%s = []" % n for n, _ in cols))
            L.append("    for (let _i = 0; _i < %s; _i++) { %s }" % (n_, " ".join("%s.push(%s);" % (n, "Number(_t[_p++])" if t in ("int", "long") else "_t[_p++]") for n, t in cols)))
            continue
        n, t = it[0], it[1]
        if t in ("int", "long"): L.append("    const %s = Number(_t[_p++]);" % n)
        elif t == "str": L.append("    const %s = _t[_p++];" % n)
        elif t == "line": L.append('    const %s = _raw.replace(/[\\r\\n]+$/, "");' % n)
        elif t in ("int[]", "long[]"): L.append("    const %s = _t.slice(_p, _p + %s).map(Number); _p += %s;" % (n, lenexpr(it[2]), lenexpr(it[2])))
        elif t == "str[]": L.append("    const %s = _t.slice(_p, _p + %s); _p += %s;" % (n, lenexpr(it[2]), lenexpr(it[2])))
        elif t == "int[][]":
            L.append("    const %s = []; for (let _i = 0; _i < %s; _i++) { %s.push(_t.slice(_p, _p + %s).map(Number)); _p += %s; }" % (n, lenexpr(it[2]), n, lenexpr(it[3]), lenexpr(it[3])))
        else: raise ValueError(t)
    L.append("    const _r = %s(%s);" % (spec["fn"], ", ".join(n for n, _ in params(spec))))
    r = spec["ret"]
    if r in ("int", "long", "str"): L.append("    console.log(String(_r));")
    elif r == "bool": L.append('    console.log(_r ? "true" : "false");')
    elif r == "bool[]/lines": L.append('    console.log(_r.map(_x => _x ? "true" : "false").join("\\n"));')
    elif r.endswith("/lines"): L.append('    console.log(_r.join("\\n"));')
    elif r == "int[][]": L.append('    console.log(_r.map(_row => _row.join(" ")).join("\\n"));')
    else: L.append('    console.log(_r.join(" "));')
    L.append("})();")
    return "\n".join(L) + "\n"


RESERVED = {"_raw", "_t", "_p", "_r", "_i", "_j", "_x", "_row", "_sb", "_rows"}


def build(spec):
    names = [it[0] for it in spec["read"] if it[0] != "rows"] + [n for it in spec["read"] if it[0] == "rows" for n, _ in it[2]]
    clash = RESERVED.intersection(names)
    if clash or "rows" in [it[0] for it in spec["read"] if len(it) == 3 and isinstance(it[2], (int, str)) and it[1] != "rows" and not isinstance(it[1], int)]:
        raise ValueError("%s: these names are used by the driver itself: %s" % (spec["fn"], sorted(clash)))
    return ({"py": py_stub(spec), "cpp": cpp_stub(spec), "java": java_stub(spec), "js": js_stub(spec)},
            {"py": {"pre": PRE["py"], "post": py_post(spec)}, "cpp": {"pre": PRE["cpp"], "post": cpp_post(spec)},
             "java": {"pre": PRE["java"], "post": java_post(spec)}, "js": {"pre": PRE["js"], "post": js_post(spec)}})


FN_DOC = ('<h3>Function to complete</h3><p>Complete <code>%s(%s)</code>. It returns %s.</p>'
          '<p class="muted">Input reading and printing are handled for you, like on LeetCode. The input format below is what the tests and <i>Custom input</i> use.</p>')


def spec_for(key, q):
    """A question's function spec: its entry in specs.py, or the "spec" field of its JSON. In the JSON the spec has
    no "ref": the question's own "ref" (class Solution with the function) is the reference."""
    if key in SPECS:
        return SPECS[key]
    s = q.get("spec")
    if not s:
        return None
    spec = dict(s)
    ref = q.get("ref", "")
    if "class Solution" not in ref:
        raise ValueError('"ref" must be a Python class Solution with the method %s(...)' % spec.get("fn"))
    spec["ref"] = ref.split("class Solution", 1)[1].split(":", 1)[1]
    return spec


def apply(q, spec):
    """Writes stub, driver and the "Function to complete" section into question q (a dict)."""
    stub, driver = build(spec)
    q["stub"], q["driver"] = stub, driver
    q["ref"] = "class Solution:" + spec["ref"].rstrip() + "\n"
    if q.get("refcpp") and "class Solution" not in q["refcpp"]:
        q["refcppProgram"] = True        # a full-program C++ reference keeps working as it is
    q["body"] = re.sub(r"<h3>Function to complete</h3>.*$", "", q["body"], flags=re.S)
    q["body"] += FN_DOC % (spec["fn"], ", ".join(n for n, _ in params(spec)), spec["returns"])
    return q


def convert(key, spec, write=True):
    company, qid = key.split("/")
    path = os.path.join(ROOT, "data", company, "questions", qid + ".json")
    with open(path, encoding="utf-8") as f:
        q = json.load(f)
    apply(q, spec)
    q["refcppProgram"] = True
    if write:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(q, f, indent=1, ensure_ascii=False)
    return q


if __name__ == "__main__":
    check = "--check" in sys.argv
    for key, spec in SPECS.items():
        convert(key, spec, write=not check)
        print(("would convert " if check else "converted ") + key)
