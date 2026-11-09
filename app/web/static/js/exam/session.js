"use strict";
// Starting and ending tests, and the code editor.

/* ---------- exam lifecycle ---------- */
function buildSet(fmt){
  if (fmt === "custom") return S.custom.filter(id => QMAP[id]);
  const out = [];
  for (const pool of FORMATS[fmt].pools){
    const ids = (typeof pool === "string" ? QS.filter(q => q.diff === pool).map(q => q.id) : pool).filter(id => QMAP[id] && !out.includes(id));
    if (ids.length) out.push(pick(ids));
  }
  return out;
}
function startExam(fmt, ids, mins, practice, untimed, cur){
  const lang = {}, code = {};
  ids.forEach(id => { const t = QMAP[id].type; lang[id] = t === "sql" ? "sql" : t === "debug" ? "js" : t === "sjt" ? "sjt" : S.lang; code[id] = {}; });
  untimed = !practice && !!untimed;
  S.exam = {fmt, ids, cur:0, start:Date.now(), dur:untimed ? 0 : mins*60000, untimed, practice:!!practice, lang, code, ans:{}, best:{}, switches:0, ended:false};
  S.exam.cur = Math.max(0, Math.min(ids.length - 1, cur || 0));
  saveExam(); S.view = "exam"; render();
}
function endExam(auto){
  const e = S.exam; if (!e || e.ended) return;
  saveCode(); e.ended = true; e.endAt = Date.now(); e.auto = !!auto; e.showReport = true;
  if (!e.practice){
    const hist = store.get(K + "-history", []);
    const total = e.ids.reduce((a, id) => a + ((e.best[id] || {}).score || 0), 0);
    hist.unshift({at:e.start, fmt:e.fmt, ids:e.ids, score:total, max:e.ids.length*100, used:e.endAt - e.start, switches:e.switches, untimed:!!e.untimed,
      per:e.ids.map(id => ({id, s:(e.best[id] || {}).score || 0}))});
    store.set(K + "-history", hist.slice(0, 30));
  }
  const bestAll = store.get(K + "-best", {});
  e.ids.forEach(id => { const s = (e.best[id] || {}).score || 0; if (s > (bestAll[id] || 0)) bestAll[id] = s; });
  store.set(K + "-best", bestAll);
  saveExam(); closeModal(); S.view = "report"; render();
}

/* ---------- editor ---------- */
let cm = null, ta = null;
function codeOf(id, lang){
  const q = QMAP[id], c = S.exam.code[id] || {}, key = bufKey(q, lang);
  if (c[key] != null) return c[key];
  // first time in HackerRank style: carry over the function you already wrote in LeetCode style
  if (key.endsWith("@hr") && c[lang] != null && c[lang] !== stubOf(q, lang)) return fullProgram(q, lang, c[lang]);
  return starterOf(q, key);
}
function saveCode(){
  if (!S.exam || S.view !== "exam") return;
  const id = S.exam.ids[S.exam.cur], lang = S.exam.lang[id];
  const v = cm ? cm.getValue() : ta ? ta.value : null;
  if (v != null){ S.exam.code[id] = S.exam.code[id] || {}; S.exam.code[id][bufKey(QMAP[id], lang)] = v; saveExam(); }
}
function mountEditor(el, value, lang){
  cm = null; ta = null;
  if (window.CodeMirror){
    cm = createEditor(el, value, lang);   // exam/editor.js
    let t; cm.on("change", () => { clearTimeout(t); t = setTimeout(saveCode, 400); });
    setTimeout(() => cm.refresh(), 0);
  } else {
    ta = document.createElement("textarea"); ta.id = "code-fallback"; ta.spellcheck = false; ta.value = value; el.appendChild(ta);
    ta.addEventListener("keydown", e => { if (e.key === "Tab"){ e.preventDefault(); const s = ta.selectionStart; ta.setRangeText("    ", s, ta.selectionEnd, "end"); } });
    ta.addEventListener("input", () => saveCode());
  }
}
