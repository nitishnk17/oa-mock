#!/usr/bin/env python3
"""Checks the generated drivers agree across languages.

For each spec, a probe "solution" in every language prints the parameters it received, then returns a fixed
value of the declared return type. Every test input must produce byte-identical output in Python, C++, Java
and JavaScript, and the returned value must print in the expected shape. Also compiles every untouched stub.

    python3 tools/style/selftest.py [company/qid ...]      (needs g++, javac/java, node)
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path[:0] = [HERE, ROOT]
from specs import SPECS          # noqa: E402
import convert                   # noqa: E402
from oa_mock import judge        # noqa: E402

RET = {  # value the probe returns, per language, and how the driver must print it
    "int": ("7", "7", "7", "7", "7"), "long": ("12345678901", "12345678901LL", "12345678901L", "12345678901", "12345678901"),
    "str": ('"a b"', '"a b"', '"a b"', '"a b"', "a b"), "bool": ("True", "true", "true", "true", "true"),
    "int[]": ("[1, 2, 3]", "{1, 2, 3}", "new int[]{1, 2, 3}", "[1, 2, 3]", "1 2 3"),
    "long[]": ("[12345678901, 2]", "{12345678901LL, 2}", "new long[]{12345678901L, 2}", "[12345678901, 2]", "12345678901 2"),
    "str[]": ('["x", "y"]', '{"x", "y"}', 'new String[]{"x", "y"}', '["x", "y"]', "x y"),
    "int[]/lines": ("[1, 2, 3]", "{1, 2, 3}", "new int[]{1, 2, 3}", "[1, 2, 3]", "1\n2\n3"),
    "long[]/lines": ("[12345678901, 2]", "{12345678901LL, 2}", "new long[]{12345678901L, 2}", "[12345678901, 2]", "12345678901\n2"),
    "str[]/lines": ('["x", "y z"]', '{"x", "y z"}', 'new String[]{"x", "y z"}', '["x", "y z"]', "x\ny z"),
    "bool[]/lines": ("[True, False]", "{true, false}", "new boolean[]{true, false}", "[true, false]", "true\nfalse"),
    "int[][]": ("[[1, 2], [3]]", "{{1, 2}, {3}}", "new int[][]{{1, 2}, {3}}", "[[1, 2], [3]]", "1 2\n3"),
}

PY_H = 'def _S(x):\n    if isinstance(x, list): return "|".join(" ".join(map(str, r)) for r in x) if x and isinstance(x[0], list) else " ".join(map(str, x))\n    return str(x)\n'
CPP_H = """string _S(long long x){return to_string(x);} string _S(const string& x){return x;}
template<class T> string _S(const vector<T>& v){string s; for(size_t i=0;i<v.size();i++){if(i) s+=' '; s+=_S(v[i]);} return s;}
string _S(const vector<vector<int>>& m){string s; for(size_t i=0;i<m.size();i++){if(i) s+='|'; s+=_S(m[i]);} return s;}
"""
JAVA_H = """    static String _S(long x){return Long.toString(x);} static String _S(String x){return x;}
    static String _S(int[] a){StringBuilder b=new StringBuilder(); for(int i=0;i<a.length;i++){if(i>0)b.append(' ');b.append(a[i]);} return b.toString();}
    static String _S(long[] a){StringBuilder b=new StringBuilder(); for(int i=0;i<a.length;i++){if(i>0)b.append(' ');b.append(a[i]);} return b.toString();}
    static String _S(String[] a){return String.join(" ", a);}
    static String _S(int[][] m){StringBuilder b=new StringBuilder(); for(int i=0;i<m.length;i++){if(i>0)b.append('|');b.append(_S(m[i]));} return b.toString();}
"""
JS_H = 'const _S = x => Array.isArray(x) ? (x.length && Array.isArray(x[0]) ? x.map(r => r.join(" ")).join("|") : x.join(" ")) : String(x);\n'


def probes(spec):
    ps = convert.params(spec); r = RET[spec["ret"]]
    names = [n for n, _ in ps]
    py = "class Solution:\n" + "\n".join("    " + l for l in PY_H.splitlines()) + "\n    def %s(self, %s):\n%s        return %s\n" % (
        spec["fn"], ", ".join(names), "".join('        print("%s=" + Solution._S(%s))\n' % (n, n) for n in names), r[0])
    py = py.replace("    def _S(x):", "    @staticmethod\n    def _S(x):")
    cpp = CPP_H + "class Solution {\npublic:\n    %s %s(%s) {\n%s        return %s;\n    }\n};\n" % (
        convert.CPP_T[convert.ret_base(spec["ret"])], spec["fn"], ", ".join(convert.cpp_param(n, t) for n, t in ps),
        "".join('        cout << "%s=" << _S(%s) << "\\n";\n' % (n, n) for n in names), r[1])
    java = "class Solution {\n" + JAVA_H + "    public %s %s(%s) {\n%s        return %s;\n    }\n}\n" % (
        convert.JAVA_T[convert.ret_base(spec["ret"])], spec["fn"], ", ".join("%s %s" % (convert.JAVA_T[t], n) for n, t in ps),
        "".join('        System.out.println("%s=" + _S(%s));\n' % (n, n) for n in names), r[2])
    js = JS_H + "var %s = function(%s) {\n%s    return %s;\n};\n" % (spec["fn"], ", ".join(names), "".join('    console.log("%s=" + _S(%s));\n' % (n, n) for n in names), r[3])
    return {"py": py, "cpp": cpp, "java": java, "js": js}, r[4]


def run_js(src, inputs):
    d = tempfile.mkdtemp(); p = os.path.join(d, "m.js"); open(p, "w").write(src); out = []
    for i in inputs:
        r = subprocess.run(["node", p], input=i.encode(), capture_output=True, timeout=60)
        out.append({"out": r.stdout.decode(), "err": r.stderr.decode() if r.returncode else ""})
    return {"results": out}


def main(keys):
    bad = 0
    for key in keys or SPECS:
        spec = SPECS[key]; company, qid = key.split("/")
        q = json.load(open(os.path.join(ROOT, "data", company, "questions", qid + ".json"), encoding="utf-8"))
        tests = [t["in"] for t in q["samples"] + q["hidden"] if len(t["in"]) < 50_000]
        stub, driver = convert.build(spec); probe, ret_text = probes(spec)
        outs = {}
        for lang in ("py", "cpp", "java", "js"):
            src = driver[lang]["pre"] + probe[lang] + driver[lang]["post"]
            res = run_js(src, tests) if lang == "js" else judge.judge(lang, src, tests, 20000)
            if "compile_error" in res:
                print("FAIL %-20s %s probe: %s" % (key, lang, res["compile_error"][-500:])); bad += 1; outs = None; break
            errs = [r["err"] for r in res["results"] if r.get("err") or r.get("tle")]
            if errs:
                print("FAIL %-20s %s probe crashed: %s" % (key, lang, errs[0][-300:])); bad += 1; outs = None; break
            outs[lang] = [r["out"].rstrip("\n") for r in res["results"]]
        if outs is None:
            continue
        same = all(outs[l] == outs["py"] for l in outs)
        shape = all(o.endswith(ret_text) for o in outs["py"])
        # untouched stubs: compile and run on sample 0
        stub_ok = []
        for lang in ("py", "cpp", "java", "js"):
            src = driver[lang]["pre"] + stub[lang] + driver[lang]["post"]
            res = run_js(src, tests[:1]) if lang == "js" else judge.judge(lang, src, tests[:1], 20000)
            ok = "compile_error" not in res and not res["results"][0].get("err") and not res["results"][0].get("tle")
            stub_ok.append(lang if ok else lang.upper() + "!")
        ok = same and shape and all(not s.endswith("!") for s in stub_ok)
        bad += not ok
        diff = "" if same else " differs: " + ", ".join(l for l in outs if outs[l] != outs["py"])
        print("%s %-20s %d inputs, 4 languages agree: %s, output shape ok: %s, stubs run: %s%s" % (
            "ok  " if ok else "FAIL", key, len(tests), same, shape, " ".join(stub_ok), diff))
        if not same:
            l = next(l for l in outs if outs[l] != outs["py"]); i = next(i for i in range(len(tests)) if outs[l][i] != outs["py"][i])
            print("      py : %r\n      %-3s: %r" % (outs["py"][i][:200], l, outs[l][i][:200]))
    print("\n" + ("all drivers agree" if not bad else "%d problem(s)" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
