"use strict";
// Score report after a test.

function reportHTML(){
  const e = S.exam;
  let ids = e.practice ? e.ids.filter(id => touched(e, id)) : e.ids;
  if (!ids.length) ids = [e.ids[e.cur]];
  const total = ids.reduce((a, id) => a + ((e.best[id] || {}).score || 0), 0), max = ids.length * 100;
  const rows = ids.map((id, i) => { const q = QMAP[id], b = e.best[id], s = b ? b.score : 0, cb = e.code[id] || {}, code = cb[bufKey(q, e.lang[id])] != null ? cb[bufKey(q, e.lang[id])] : cb[e.lang[id]] != null ? cb[e.lang[id]] : cb[e.lang[id] + "@hr"];
    return `<div class="rq"><div class="rq-head"><span class="pill d-${q.diff}">${q.diff}</span><span class="t">${e.practice ? "" : `Q${i + 1}. `}${esc(q.title)}</span><span class="sc">${s}/100</span></div>
      <div class="bar-meter" aria-hidden="true"><i style="width:${s}%"></i></div>
      <div class="status">${q.type === "sjt" ? `${sjtAnswered(q, e.ans && e.ans[id])}/${q.items.length} answered · ${b ? b.passed : 0}/${sjtMax(q)} points` : b ? `${b.passed}/${b.total} tests passed · ${LANGS[b.lang].label}` : "Not submitted"}</div>
      ${code ? `<details class="sol"><summary>Your code</summary><pre>${esc(code)}</pre></details>` : ""}
      ${q.lc ? `<div class="status">Practise the same pattern: ${q.lcurl ? `<a href="${esc(q.lcurl)}" target="_blank" rel="noopener">${esc(q.lc)}</a>` : esc(q.lc)}</div>` : ""}
      ${q.type === "sjt" ? sjtReview(q, (e.ans && e.ans[id]) || {}) : `<details class="sol"><summary>Reference solution${q.type === "sql" ? " (SQL)" : q.type === "debug" ? " (fixed files, JavaScript)" : " (Python)"}</summary><pre>${esc(q.ref)}</pre></details>`}
      ${q.fixnotes ? `<details class="sol"><summary>What was broken</summary>${q.fixnotes}</details>` : ""}
      ${q.refcpp ? `<details class="sol"><summary>Reference solution (C++)</summary><pre>${esc(q.refcpp)}</pre></details>` : ""}</div>`; }).join("");
  return `
  <header class="bar"><div class="brand">${e.practice ? "Practice finished" : "Test report"}<small>${e.auto ? "time ran out" : "ended by you"}</small></div><div class="spacer"></div>${LOCAL ? `<a class="btn" href="/">All companies</a>` : ""}<button class="btn" id="home">⌂ Home</button></header>
  <main class="wrap">
    <section class="panel">
      <div class="score-big">${total}<small> / ${max}</small></div>
      <div class="kpis"><span>Time used <b>${fmtTime((e.endAt || Date.now()) - e.start)}</b></span>${e.practice ? "" : `<span>Time allowed <b>${e.untimed ? "no limit" : fmtTime(e.dur)}</b></span><span>Tab switches <b>${e.switches}</b></span>`}<span>Fully solved <b>${ids.filter(id => (e.best[id] || {}).score === 100).length}/${ids.length}</b></span></div>
    </section>
    <section class="panel"><h2>Per question</h2>${rows}</section>
    <div class="report-nav"><button class="btn primary" id="home2">⌂ Back to ${esc(CFG.name.replace(/ Mock$/, ""))} home</button><button class="btn" id="again">${e.practice ? "Practise again" : "Start another test"}</button>${LOCAL ? `<a class="btn" href="/">All companies</a>` : ""}</div>
  </main>`;
}
function sjtReview(q, ans){
  return `<details class="sol"><summary>Review your answers</summary>${q.items.map((it, i) => { const mine = ans[i], best = it.o.findIndex(o => o[1] === 2);
    return `<div style="border-top:1px solid var(--line);padding:10px 0"><p style="margin:0 0 6px"><b>${i + 1}.</b> ${esc(it.s)}</p>
      <p class="status" style="margin:0">Your answer: ${mine == null ? "not answered" : esc(it.o[mine][0]) + ` <b>(${it.o[mine][1]}/2)</b>`}</p>
      ${mine !== best ? `<p class="status" style="margin:4px 0 0">Best: ${esc(it.o[best][0])}</p>` : ""}
      <p class="sjt-why"><b>${esc(it.lp)}.</b> ${esc(it.why)}</p></div>`; }).join("")}</details>`;
}
function bindReport(){
  const home = () => { S.exam.showReport = false; saveExam(); S.view = "home"; render(); };
  $("#home").addEventListener("click", home); $("#home2").addEventListener("click", home);
  $("#again").addEventListener("click", () => { const e = S.exam; if (e.practice) startExam("practice", e.ids, 0, true, false, e.cur); else home(); });
}
