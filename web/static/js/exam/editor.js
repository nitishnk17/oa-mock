"use strict";
// The code editor (CodeMirror 5): settings, smart indentation, autocomplete, snippets, shortcuts.

const IS_MAC = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
const MOD = IS_MAC ? "Cmd" : "Ctrl";

/* ---------- settings (saved in this browser) ---------- */
const ED_DEFAULTS = {
  highlight: true,        // syntax highlighting
  autocomplete: true,     // suggestions while typing
  snippets: true,         // fori, sout, ... in suggestions
  closeBrackets: true,    // type ( and get )
  matchBrackets: true,
  activeLine: true,
  matchWords: true,       // highlight other occurrences of the word under the cursor
  fold: true,             // fold arrows in the gutter
  lineWrap: false,
  keymap: "sublime",      // sublime (VS Code-like) | default | vim
  tabSize: 4,
  fontSize: 14,
};
const ED = Object.assign({}, ED_DEFAULTS, store.get("oa-editor", {}));
const saveED = () => store.set("oa-editor", ED);

/* ---------- autocomplete words ---------- */
const WORDS = {
  py: `False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield
    print input range len int str float bool list dict set tuple sorted reversed enumerate zip map filter sum min max abs any all isinstance ord chr pow divmod bin hex round open super object
    self append extend insert pop remove index count sort reverse keys values items get setdefault update join split strip lstrip rstrip startswith endswith replace find upper lower isdigit isalpha
    sys math collections heapq bisect itertools functools defaultdict Counter deque OrderedDict heappush heappop heapify nlargest nsmallest bisect_left bisect_right insort lru_cache cache reduce
    accumulate permutations combinations product groupby gcd lcm inf sqrt isqrt floor ceil log log2 comb stdin stdout readline setrecursionlimit List Optional Dict Tuple Set
    ValueError KeyError IndexError Exception float('inf')`,
  cpp: `alignas auto bool break case catch char class const constexpr continue default delete do double else enum explicit extern false float for friend goto if inline int long mutable namespace new
    nullptr operator private protected public return short signed sizeof static static_cast struct switch template this throw true try typedef typename union unsigned using virtual void volatile while
    include bits/stdc++.h iostream std vector string map unordered_map set unordered_set multiset multimap pair make_pair tuple tie priority_queue queue deque stack bitset array list
    sort stable_sort reverse lower_bound upper_bound binary_search accumulate min max min_element max_element swap abs gcd lcm memset fill iota unique next_permutation count find
    push_back emplace_back pop_back emplace begin end rbegin rend size empty clear insert erase front back top push pop first second resize assign substr length
    cin cout cerr endl getline to_string stoi stoll INT_MAX INT_MIN LLONG_MAX LLONG_MIN numeric_limits greater less function ios sync_with_stdio tie size_t int64_t`,
  java: `abstract boolean break byte case catch char class continue default do double else enum extends final finally float for if implements import instanceof int interface long new null
    package private protected public return short static super switch this throw throws true false try void while var
    System out println print printf String StringBuilder Scanner BufferedReader InputStreamReader StringTokenizer Integer Long Double Character Math Arrays Collections Comparator Objects
    List ArrayList LinkedList Map HashMap TreeMap LinkedHashMap Set HashSet TreeSet Queue Deque ArrayDeque PriorityQueue Stack Iterator
    add get set put getOrDefault containsKey containsValue remove offer poll peek push pop isEmpty size clear contains sort asList fill stream length charAt toCharArray substring
    append toString valueOf parseInt parseLong MAX_VALUE MIN_VALUE nextInt nextLine readLine nextToken split trim equals compareTo hashCode`,
  js: `break case catch class const continue default delete do else export extends false finally for function if in instanceof let new null return super switch this throw true try typeof
    undefined var void while yield async await of console log Math max min floor ceil abs sqrt pow Array Map Set Object Number String BigInt JSON parseInt parseFloat keys values entries
    push pop shift unshift slice splice sort map filter reduce forEach find findIndex includes indexOf join split length fill from has get set add delete size require readFileSync trim`,
  sql: `SELECT FROM WHERE GROUP BY HAVING ORDER ASC DESC JOIN LEFT RIGHT INNER OUTER ON AS AND OR NOT IN IS NULL LIKE BETWEEN DISTINCT COUNT SUM AVG MIN MAX ROUND LIMIT UNION ALL CASE WHEN THEN ELSE END`,
};
for (const k in WORDS) WORDS[k] = [...new Set(WORDS[k].split(/\s+/).filter(Boolean))];

// "$0" marks where the cursor goes; "\t" is one indent level (relative to the line you type on)
const SNIPPETS = {
  py: [["fori", "for i in range(n):\n\t$0", "for i in range(n)"], ["forin", "for x in arr:\n\t$0", "for x in arr"],
       ["def", "def name(self):\n\t$0", "method"], ["ifmain", 'if __name__ == "__main__":\n\t$0', "main guard"],
       ["readints", "list(map(int, input().split()))$0", "read a line of ints"], ["memo", "@lru_cache(maxsize=None)\ndef dfs(i):\n\t$0", "memoised recursion"]],
  cpp: [["fori", "for (int i = 0; i < n; i++) {\n\t$0\n}", "for (int i ...)"], ["forr", "for (auto& x : v) {\n\t$0\n}", "range-for"],
        ["whilel", "while ($0) {\n\t\n}", "while"], ["vi", "vector<int>$0", "vector<int>"], ["vvi", "vector<vector<int>>$0", "vector<vector<int>>"],
        ["vll", "vector<long long>$0", "vector<long long>"], ["pii", "pair<int, int>$0", "pair<int, int>"], ["ll", "long long$0", "long long"],
        ["all", "v.begin(), v.end()$0", "begin, end"], ["fastio", "ios::sync_with_stdio(false);\ncin.tie(nullptr);\n$0", "fast I/O"]],
  java: [["fori", "for (int i = 0; i < n; i++) {\n\t$0\n}", "for (int i ...)"], ["foreach", "for (int x : arr) {\n\t$0\n}", "for-each"],
         ["sout", "System.out.println($0);", "System.out.println"], ["map", "Map<Integer, Integer> map = new HashMap<>();$0", "HashMap"],
         ["list", "List<Integer> list = new ArrayList<>();$0", "ArrayList"]],
  js: [["fori", "for (let i = 0; i < n; i++) {\n\t$0\n}", "for (let i ...)"], ["forof", "for (const x of arr) {\n\t$0\n}", "for...of"],
       ["log", "console.log($0);", "console.log"]],
};

function langOfMode(cmi){ return cmi.getOption("oaLang") || "py"; }

function applySnippet(cmi, data, item){
  const from = data.from, base = cmi.getLine(from.line).match(/^\s*/)[0], unit = " ".repeat(cmi.getOption("indentUnit"));
  const lines = item.snippet.split("\n").map((l, i) => (i ? base : "") + l.replace(/\t/g, unit));
  let text = lines.join("\n"), cursor = null;
  const at = text.indexOf("$0");
  if (at >= 0){
    const pre = text.slice(0, at).split("\n");
    cursor = {line: from.line + pre.length - 1, ch: (pre.length === 1 ? from.ch : 0) + pre[pre.length - 1].length};
    text = text.replace("$0", "");
  }
  cmi.replaceRange(text, from, data.to, "complete");
  if (cursor) cmi.setCursor(cursor);
}

function oaHint(cmi){
  const cur = cmi.getCursor(), line = cmi.getLine(cur.line);
  let start = cur.ch; while (start > 0 && /[\w$]/.test(line[start - 1])) start--;
  const word = line.slice(start, cur.ch);
  if (!word) return null;
  const lang = langOfMode(cmi), seen = new Set([word]), list = [];
  const add = (text, cls, extra) => { if (!seen.has(text) && text.startsWith(word)) { seen.add(text); list.push(Object.assign({text, className:cls}, extra)); } };
  // snippets also match when you've typed the whole trigger ("fori")
  if (ED.snippets) for (const [key, body, desc] of SNIPPETS[lang] || []) if (key.startsWith(word)) list.push({text:key, className:"hint-snippet", displayText:key + "  ·  " + desc, snippet:body, hint:applySnippet});
  // identifiers already in the file come first: they're what you're most likely to reuse
  const docWords = cmi.getValue().match(/[A-Za-z_$][\w$]{1,}/g) || [];
  const freq = {}; for (const w of docWords) freq[w] = (freq[w] || 0) + 1;
  freq[word] = (freq[word] || 1) - 1;
  Object.keys(freq).filter(w => freq[w] > 0).sort((a, b) => freq[b] - freq[a]).forEach(w => add(w, "hint-word"));
  for (const w of WORDS[lang] || []) add(w, "hint-kw");
  if (!list.length) return null;
  return {list:list.slice(0, 60), from:CodeMirror.Pos(cur.line, start), to:CodeMirror.Pos(cur.line, cur.ch)};
}

/* ---------- indentation ---------- */
function tabKey(cmi){
  if (cmi.state.completionActive) return CodeMirror.Pass;
  if (cmi.somethingSelected()) return cmi.execCommand("indentMore");
  const unit = cmi.getOption("indentUnit"), cur = cmi.getCursor();
  cmi.replaceSelection(" ".repeat(unit - (cur.ch % unit)), "end", "+input");
}
function backspaceKey(cmi){
  if (cmi.somethingSelected()) return CodeMirror.Pass;
  const cur = cmi.getCursor(), before = cmi.getLine(cur.line).slice(0, cur.ch);
  if (cur.ch === 0 || !/^ +$/.test(before)) return CodeMirror.Pass;
  const unit = cmi.getOption("indentUnit"), target = Math.floor((cur.ch - 1) / unit) * unit;
  cmi.replaceRange("", CodeMirror.Pos(cur.line, target), cur, "+delete");
}
function reindentAll(cmi){
  const sel = cmi.somethingSelected();
  const from = sel ? cmi.getCursor("from").line : 0, to = sel ? cmi.getCursor("to").line : cmi.lineCount() - 1;
  cmi.operation(() => { for (let i = from; i <= to; i++) cmi.indentLine(i, "smart"); });
  toast("Re-indented " + (to - from + 1) + (to === from ? " line" : " lines"));
}
// In C++/Java/JS, typing "}" on an otherwise empty line right above an auto-inserted "}" would leave two.
// Swallow it and just move past the existing one.
function closeBraceKey(cmi){
  if (!ED.closeBrackets || cmi.somethingSelected() || cmi.getOption("oaLang") === "py") return CodeMirror.Pass;
  const cur = cmi.getCursor(), here = cmi.getLine(cur.line), next = cmi.getLine(cur.line + 1);
  if (here.trim() !== "" || next == null || next.trim() !== "}") return CodeMirror.Pass;
  if (here.length < next.match(/^\s*/)[0].length) return CodeMirror.Pass;
  // only when every "{" already has its "}", i.e. the one below was inserted for us
  const src = cmi.getValue().replace(/\/\/.*|\/\*[\s\S]*?\*\/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'/g, "");
  if ((src.match(/{/g) || []).length !== (src.match(/}/g) || []).length) return CodeMirror.Pass;
  cmi.operation(() => {
    cmi.replaceRange("", CodeMirror.Pos(cur.line, 0), CodeMirror.Pos(cur.line + 1, 0));
    cmi.setCursor(CodeMirror.Pos(cur.line, cmi.getLine(cur.line).indexOf("}") + 1));
  });
}

/* ---------- shortcuts (also listed in the help dialog) ---------- */
const SHORTCUTS = [
  ["Run samples", `${MOD}+Enter`], ["Submit", `${MOD}+Shift+Enter`], ["Save now", `${MOD}+S`],
  ["Suggestions", "Ctrl+Space"], ["Indent / dedent", "Tab / Shift+Tab"], ["Re-indent file or selection", `${MOD}+Shift+I`],
  ["Toggle comment", `${MOD}+/`], ["Find / replace", IS_MAC ? "Cmd+F / Cmd+Option+F" : "Ctrl+F / Ctrl+H"], ["Go to line", "Ctrl+G"],
  ["Select next occurrence (multi-cursor)", `${MOD}+D`], ["Select line", `${MOD}+L`], ["Duplicate line", `${MOD}+Shift+D`], ["Delete line", "Ctrl+Shift+K"],
  ["Move line up / down", IS_MAC ? "Cmd+Ctrl+↑ / ↓" : "Ctrl+Shift+↑ / ↓"], ["Add cursor above / below", IS_MAC ? "Ctrl+Shift+↑ / ↓" : "Ctrl+Alt+↑ / ↓"],
  ["Jump to matching bracket", `${MOD}+M`], ["Fold / unfold block", "Ctrl+Q"], ["Undo / redo", `${MOD}+Z / ${MOD}+Shift+Z`],
  ["Previous / next question", "Alt+PageUp / PageDown (or Alt+← / → outside the editor)"], ["Shortcut help", "F1"],
];

function editorKeys(){
  const k = {   // checked before the key style (Sublime/Vim), so Run/Submit always win
    Tab: tabKey, "Shift-Tab": c => c.execCommand("indentLess"), Backspace: backspaceKey, "'}'": closeBraceKey,
    "Ctrl-Space": c => c.showHint({hint:oaHint, completeSingle:false}),
    "Ctrl-Enter": () => doRun(false), "Cmd-Enter": () => doRun(false), "Shift-Ctrl-Enter": () => doRun(true), "Shift-Cmd-Enter": () => doRun(true),
    "Ctrl-S": () => { saveCode(); toast("Saved"); }, "Cmd-S": () => { saveCode(); toast("Saved"); },
    "Shift-Ctrl-I": reindentAll, "Shift-Cmd-I": reindentAll,
    "Ctrl-/": c => c.toggleComment({indent:true}), "Cmd-/": c => c.toggleComment({indent:true}),
    "Ctrl-Q": c => c.foldCode(c.getCursor()),
    "Ctrl-G": "jumpToLine", "Ctrl-H": "replace", "Cmd-Alt-F": "replace",
    "Alt-PageDown": () => S.exam && goQ(S.exam, S.exam.cur + 1), "Alt-PageUp": () => S.exam && goQ(S.exam, S.exam.cur - 1),
    F1: () => showShortcuts(),
  };
  return k;
}

function foldFinder(lang){
  if (!CodeMirror.fold) return undefined;
  return lang === "py" ? CodeMirror.fold.indent : CodeMirror.fold.combine(CodeMirror.fold.brace, CodeMirror.fold.comment);
}

function editorOptions(lang){
  return {
    mode: LANGS[lang].mode, oaLang: lang, lineNumbers: true, indentUnit: ED.tabSize, tabSize: ED.tabSize, indentWithTabs: false,
    smartIndent: true, electricChars: true, matchBrackets: ED.matchBrackets, autoCloseBrackets: ED.closeBrackets ? "()[]{}''\"\"" : false,
    styleActiveLine: ED.activeLine, lineWrapping: ED.lineWrap, keyMap: ED.keymap === "default" ? "default" : ED.keymap,
    highlightSelectionMatches: ED.matchWords ? {showToken: /[\w$]/, minChars: 2, delay: 150} : false,
    foldGutter: ED.fold, foldOptions: {rangeFinder: foldFinder(lang), widget: "⋯"},
    gutters: ED.fold ? ["CodeMirror-linenumbers", "CodeMirror-foldgutter"] : ["CodeMirror-linenumbers"],
    extraKeys: editorKeys(), hintOptions: {hint: oaHint, completeSingle: false},
  };
}

CodeMirror.defineOption("oaLang", "py", () => {});

function createEditor(el, value, lang){
  const cmi = CodeMirror(el, Object.assign({value}, editorOptions(lang)));
  cmi.on("inputRead", (c, ch) => {
    if (!ED.autocomplete || c.state.completionActive || ch.origin !== "+input") return;
    const t = ch.text.join("");
    if (!/^[\w$]$/.test(t)) return;
    const cur = c.getCursor(), line = c.getLine(cur.line).slice(0, cur.ch), w = line.match(/[\w$]+$/);
    const tok = c.getTokenAt(cur);
    if (w && w[0].length >= 2 && !/comment|string/.test(tok.type || "")) c.showHint({hint: oaHint, completeSingle: false});
  });
  applyEditorLook(el);
  return cmi;
}

function applyEditorLook(el){
  const host = el || document.getElementById("editor");
  if (!host) return;
  host.classList.toggle("no-hl", !ED.highlight);
  host.style.setProperty("--ed-font", ED.fontSize + "px");
}

function setEditorOption(key, value){
  ED[key] = value; saveED();
  if (!cm) return;
  const lang = cm.getOption("oaLang"), o = editorOptions(lang);
  const map = {matchBrackets:["matchBrackets"], closeBrackets:["autoCloseBrackets"], activeLine:["styleActiveLine"], lineWrap:["lineWrapping"],
               keymap:["keyMap"], matchWords:["highlightSelectionMatches"], fold:["foldGutter", "gutters"], tabSize:["indentUnit", "tabSize"]};
  for (const opt of map[key] || []) cm.setOption(opt, o[opt]);
  applyEditorLook();
  cm.refresh();
}

/* ---------- settings popover and shortcut help ---------- */
function editorSettingsHTML(){
  const ck = (k, label, hint) => `<label class="ed-row" title="${esc(hint || "")}"><input type="checkbox" data-ed="${k}" ${ED[k] ? "checked" : ""}> ${label}</label>`;
  return `<div class="popover" id="edpop" role="dialog" aria-label="Editor settings">
    <div class="ed-grid">
      <div><div class="ed-h">Help while typing</div>
        ${ck("autocomplete", "Suggestions as you type", "Ctrl+Space shows them any time")}
        ${ck("snippets", "Snippets (fori, sout, vi…)")}
        ${ck("closeBrackets", "Auto-close brackets and quotes")}
        ${ck("highlight", "Syntax highlighting")}
        ${ck("matchBrackets", "Highlight matching bracket")}
        ${ck("matchWords", "Highlight other uses of a word")}</div>
      <div><div class="ed-h">View</div>
        ${ck("activeLine", "Highlight current line")}
        ${ck("fold", "Code folding")}
        ${ck("lineWrap", "Wrap long lines")}
        <label class="ed-row">Font size <select data-ed="fontSize">${[12, 13, 14, 15, 16, 18, 20].map(n => `<option ${ED.fontSize === n ? "selected" : ""}>${n}</option>`).join("")}</select></label>
        <label class="ed-row">Indent <select data-ed="tabSize">${[2, 4].map(n => `<option value="${n}" ${ED.tabSize === n ? "selected" : ""}>${n} spaces</option>`).join("")}</select></label>
        <label class="ed-row" title="LeetCode: you write a function and a hidden driver reads the input. HackerRank: you get the whole program, input reading included.">Problem style <select id="ed-style"><option value="leetcode" ${STYLE === "leetcode" ? "selected" : ""}>LeetCode</option><option value="hackerrank" ${STYLE === "hackerrank" ? "selected" : ""}>HackerRank</option></select></label>
        <label class="ed-row">Keys <select data-ed="keymap">${[["sublime", "VS Code / Sublime"], ["default", "Basic"], ["vim", "Vim"]].map(([v, l]) => `<option value="${v}" ${ED.keymap === v ? "selected" : ""}>${l}</option>`).join("")}</select></label></div>
    </div>
    <div class="ed-foot"><button class="btn" id="ed-keys">⌨ Keyboard shortcuts</button><button class="btn" id="ed-reset">Restore defaults</button></div>
  </div>`;
}
function bindEditorSettings(){
  const btn = $("#edset"); if (!btn) return;
  btn.addEventListener("click", ev => {
    ev.stopPropagation();
    const open = $("#edpop"); if (open){ open.remove(); return; }
    btn.insertAdjacentHTML("afterend", editorSettingsHTML());
    const pop = $("#edpop");
    pop.addEventListener("click", e => e.stopPropagation());
    pop.querySelectorAll("[data-ed]").forEach(inp => inp.addEventListener("change", () => {
      const k = inp.dataset.ed, v = inp.type === "checkbox" ? inp.checked : (k === "keymap" ? inp.value : +inp.value);
      setEditorOption(k, v);
    }));
    $("#ed-keys").addEventListener("click", () => { pop.remove(); showShortcuts(); });
    $("#ed-style").addEventListener("change", ev => { pop.remove(); setStyle(ev.target.value); toast(ev.target.value === "hackerrank" ? "HackerRank style: the whole program is in the editor" : "LeetCode style: write the function, the I/O is hidden"); });
    $("#ed-reset").addEventListener("click", () => { for (const k in ED_DEFAULTS) setEditorOption(k, ED_DEFAULTS[k]); pop.remove(); toast("Editor settings restored"); });
    setTimeout(() => document.addEventListener("click", function close(){ const p = $("#edpop"); if (p) p.remove(); document.removeEventListener("click", close); }), 0);
  });
}
function showShortcuts(){
  const m = $("#modal");
  m.innerHTML = `<div class="box wide" role="dialog" aria-modal="true" aria-labelledby="m-t"><h3 id="m-t" style="font-size:20px">Keyboard shortcuts</h3>
    <table class="keys-table">${SHORTCUTS.map(([a, k]) => `<tr><td>${esc(a)}</td><td><kbd>${esc(k)}</kbd></td></tr>`).join("")}</table>
    <p class="muted" style="margin:0">Key style: ${ED.keymap === "vim" ? "Vim (Esc for normal mode)" : ED.keymap === "sublime" ? "VS Code / Sublime" : "basic"}. Change it under ⚙ Editor.</p>
    <div class="row"><button class="btn primary" id="m-no">Close</button></div></div>`;
  m.hidden = false; $("#m-no").focus(); $("#m-no").onclick = () => { closeModal(); if (cm) cm.focus(); };
}
function toast(msg){
  let t = $("#toast");
  if (!t){ t = document.createElement("div"); t.id = "toast"; t.className = "toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
  t.textContent = msg; t.classList.add("show"); clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("show"), 1600);
}
