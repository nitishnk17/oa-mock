"use strict";
// Question data, company config, languages and saved state.

const QS = window.OA_DATA.questions;
const QMAP = Object.fromEntries(QS.map(q => [q.id, q]));
const CFG = window.OA_DATA.config;
const K = CFG.key;
const OFFLIST = CFG.offlist;
const FORMATS = CFG.formats;
const LOCAL = !!window.LOCAL_JUDGE;   // set by the server; C++, Java and Python run there
const LANGS = {py:{label:"Python 3", mode:"python"}, cpp:{label:"C++17", mode:"text/x-c++src"}, java:{label:"Java", mode:"text/x-java"}, js:{label:"JavaScript (Node)", mode:"javascript"}, sql:{label:"SQL", mode:"text/x-sql"}};
const CODE_LANGS = ["py", "cpp", "java", "js"];
const NEEDS_LOCAL = l => (l === "cpp" || l === "java") && !LOCAL;
const STARTER = {
  py:`import sys\n\ndef main():\n    data = sys.stdin.read().split()\n    # write your solution here and print the answer\n\nmain()\n`,
  js:`const data = require("fs").readFileSync(0, "utf8").trim().split(/\\s+/);\n\n// write your solution here and print with console.log\n`,
  cpp:`#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    // read input from STDIN and print the answer\n\n    return 0;\n}\n`,
  java:`import java.util.*;\nimport java.io.*;\n\npublic class Main {\n    public static void main(String[] args) throws IOException {\n        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n        // read input and print the answer\n    }\n}\n`,
  sql:`-- Write one query. Tables: companies, departments, employees\nSELECT \n`
};
const LIMIT = LOCAL ? {py:5000, js:4000, cpp:2000, java:4000} : {py:8000, js:4000, cpp:2000, java:4000};

/* ---------- storage ---------- */
const store = {
  get(k, d){ try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch(e){ return d; } },
  set(k, v){ try { localStorage.setItem(k, JSON.stringify(v)); } catch(e){} }
};
let S = { view:"home", exam:store.get(K + "-exam", null), fmt:CFG.defaultFmt, custom:CFG.custom.slice(), customMins:60, lang:store.get(K + "-lang","py"), untimed:store.get(K + "-untimed", false) };
if (S.exam && !S.exam.ended) S.view = "exam"; else if (S.exam && S.exam.ended && S.exam.showReport) S.view = "report";
const saveExam = () => store.set(K + "-exam", S.exam);
