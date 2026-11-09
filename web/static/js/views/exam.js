"use strict";
// Test page markup: statement, editor, top bar, SJT page.

function stmtHTML(q){
  const samples = q.type === "sql"
    ? q.samples.map((s, i) => `<h3>Sample data ${i}</h3>${Object.entries(s.tables).map(([t, d]) => tableHTML(t, d.cols, d.rows)).join("")}<h3>Expected output ${i}</h3>${tableHTML("result", ["company_name", "department_name", "average_salary"], s.out)}<p class="ex">${esc(s.ex)}</p>`).join("")
    : STYLE === "hackerrank"
      ? q.samples.map((s, i) => `<h3>Sample Input ${i}</h3><pre>${esc(s.in)}</pre><h3>Sample Output ${i}</h3><pre>${esc(s.out)}</pre>${s.ex ? `<h3>Explanation ${i}</h3><p class="ex">${esc(s.ex)}</p>` : ""}`).join("")
      : q.samples.map((s, i) => `<h3>Example ${i + 1}</h3><div class="sample"><div><div class="lbl">Input</div><pre>${esc(s.in)}</pre></div><div><div class="lbl">Output</div><pre>${esc(s.out)}</pre></div></div>${s.ex ? `<p class="ex"><b>Explanation:</b> ${esc(s.ex)}</p>` : ""}`).join("");
  const schema = q.schema ? `<h3>Tables</h3>${q.schema.map(t => `<p><code>${t.t}</code>(${t.cols.map(c => `${c[0]} <span class="muted">${c[1]}</span>`).join(", ")})</p>`).join("")}` : "";
  const lc = S.exam && S.exam.practice && q.lc ? ` · <a href="${esc(q.lcurl || "#")}" target="_blank" rel="noopener">${esc(q.lc)}</a>` : "";
  const tags = qTags(q).map(t => `<span class="tag">${esc(String(t))}</span>`).join("");
  const head = `<div class="meta"><span class="pill d-${q.diff}">${q.diff}</span>${tags}<span>${esc(q.src)}${lc}</span></div><h2>${esc(q.title)}</h2>`;
  const cons = `<h3>Constraints</h3><ul>${q.cons.map(c => `<li>${c}</li>`).join("")}</ul>`;
  const fmt = `<h3>Input format</h3><p>${q.inp}</p><h3>Output format</h3><p>${q.out}</p>`;
  const lang = S.exam && S.exam.lang ? S.exam.lang[q.id] : null;
  if (STYLE === "hackerrank" || !hasDriver(q, lang || "py")){
    const body = hasDriver(q, lang || "py") ? q.body.replace(/<p class="muted">Input reading and printing are handled for you[^<]*(<i>[^<]*<\/i>[^<]*)?<\/p>/,
      '<p class="muted">The editor holds the whole program: reading the input and printing the result are already written, so complete the function. You may also rewrite the I/O yourself.</p>') : q.body;
    return head + body + schema + fmt + cons + samples;
  }
  return head + q.body + schema + samples + cons + `<details class="iofmt"><summary>Input and output format (for Custom input)</summary>${fmt}</details>`;
}
function tableHTML(name, cols, rows){
  return `<div class="scroll-x"><table class="dtable"><caption>${esc(name)}</caption><thead><tr>${cols.map(c => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${rows.length ? rows.map(r => `<tr>${r.map(v => `<td>${esc(typeof v === "number" && !Number.isInteger(v) ? v.toFixed(4) : v)}</td>`).join("")}</tr>`).join("") : `<tr><td colspan="${cols.length}" class="muted">no rows</td></tr>`}</tbody></table></div>`;
}

function examHTML(){
  const e = S.exam, id = e.ids[e.cur], q = QMAP[id], lang = e.lang[id];
  const tabs = e.ids.map((x, i) => { const b = e.best[x], qq = QMAP[x], na = qq.type === "sjt" ? sjtAnswered(qq, e.ans && e.ans[x]) : 0;
    const cls = qq.type === "sjt" ? (na === qq.items.length ? "full" : na ? "part" : "") : !b ? "" : b.score === 100 ? "full" : b.score > 0 ? "part" : ""; return `<button class="qtab" data-q="${i}" aria-current="${i === e.cur}" title="${esc(qq.title)}">Q${i + 1}<span class="dot ${cls}"></span></button>`; }).join("");
  if (q.type === "sjt") return examBar(e, tabs) + sjtHTML(q, e);
  const langs = q.type === "sql" ? ["sql"] : q.type === "debug" ? ["js"] : CODE_LANGS;
  return examBar(e, tabs) + `
  <div class="exam">
    <article class="stmt" id="stmt">${stmtHTML(q)}</article>
    <div class="rz-v" id="rz-v" role="separator" aria-orientation="vertical" aria-label="Resize the problem panel" tabindex="0"></div>
    <section class="work" aria-label="Code editor">
      <div class="toolbar">
        ${langPickerHTML(langs, lang, "Language: " + (q.type === "sql" ? "SQL engine: AlaSQL" : lang === "js" ? "JavaScript runs in your browser" : "runs on your computer"))}
        <button class="btn" id="reset" title="Replace the code with the starter template">Reset</button>
        <button class="btn" id="subs-btn" title="Your past submissions for this question">Submissions</button>
        <span class="ed-wrap"><button class="icon-btn" id="edset" title="Editor and appearance settings: suggestions, brackets, font size, keys, theme…" aria-haspopup="dialog" aria-label="Editor settings"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 4.5h7M12.5 4.5h1M2.5 11.5h1M6.5 11.5h7"/><circle cx="11" cy="4.5" r="1.5"/><circle cx="5" cy="11.5" r="1.5"/></svg></button></span>
        <span class="status" id="rt">${runtimeNote(q, lang)}</span>
        <div class="spacer"></div>
        <button class="btn" id="run">Run code</button>
        <button class="btn primary" id="submit">Submit code</button>
      </div>
      <div class="editor" id="editor"></div>
      <div class="console${UI.min ? " min" : ""}" id="console" style="height:${UI.ch}px">
        <div class="rz-h" id="rz-h" role="separator" aria-orientation="horizontal" aria-label="Resize the test results panel" tabindex="0"></div>
        <div class="console-bar">
          <button class="ctoggle" id="ctoggle" aria-expanded="${!UI.min}" aria-controls="cbody"><span class="chev" aria-hidden="true">▾</span> Test results</button>
          <span class="cstat" id="cstat"></span>
          <div class="spacer"></div>
          ${q.type === "sql" ? "" : `<label for="usecustom" class="status"><input type="checkbox" id="usecustom"> Custom input</label>`}
          <span class="status keys">${MOD}+Enter run · ${MOD}+Shift+Enter submit · <button class="linkbtn" id="keys-help">F1 all shortcuts</button></span>
        </div>
        <div class="console-body" id="cbody">
          <textarea class="custom-in" id="custom" hidden placeholder="Type custom input here"></textarea>
          <div id="out">${NEEDS_LOCAL(lang) ? localHelp() : langMissing(lang) ? missingHelp(lang) : `<p class="muted">Run your code to see the results here.</p>`}</div>
        </div>
      </div>
    </section>
  </div>`;
}
function runtimeNote(q, lang){
  return q.type === "sql" ? "SQL engine: AlaSQL" : NEEDS_LOCAL(lang) ? "Needs the local runner"
    : langMissing(lang) ? (OAInstall.installing(lang) ? "Installing " + OAInstall.NAME[lang] + "…" : LANGS[lang].label + " isn't installed on this computer")
    : LOCAL && lang !== "js" ? "Runs on your computer" + (lang === "cpp" ? " (g++)" : lang === "java" ? " (javac)" : " (python)")
    : lang === "py" ? "Python runs in your browser (first run loads it)" : "JavaScript runs in your browser";
}
function examBar(e, tabs){
  return `
  <header class="bar">
    <div class="brand">${e.practice ? "Practice" : esc(FORMATS[e.fmt] ? FORMATS[e.fmt].name + " mock" : "Mock")}<small>${e.practice ? "untimed · solution available" : e.ids.length + " questions" + (e.untimed ? " · no timer" : "")}</small></div>
    <button class="btn" id="nav-home" title="Go to the home page. ${e.practice ? "Your code is kept" : "The test keeps running"}; resume from there.">Home</button>
    <div class="navgrp">
      <button class="btn" id="prev" ${e.cur === 0 ? "disabled" : ""} title="Previous question" aria-label="Previous question">‹ Prev</button>
      ${e.practice ? `<select id="qpick" aria-label="Question">${e.ids.map((x, i) => { const b = e.best[x]; return `<option value="${i}" ${i === e.cur ? "selected" : ""}>${i + 1}. ${esc(QMAP[x].title)}${b ? ` (${b.score}/100)` : ""}</option>`; }).join("")}</select>` : `<nav class="qtabs" aria-label="Questions">${tabs}</nav>`}
      <button class="btn" id="next" ${e.cur === e.ids.length - 1 ? "disabled" : ""} title="Next question" aria-label="Next question">Next ›</button>
    </div>
    <div class="spacer"></div>
    ${e.practice ? "" : e.untimed ? `<div class="timer" id="timer" aria-live="off" title="Time elapsed. There is no limit."><span class="lbl">elapsed</span><span id="tval">00:00</span></div>` : `<div class="timer" id="timer" aria-live="off">--:--</div>`}
    <button class="btn danger" id="end">${e.practice ? "Finish" : "End test"}</button>
  </header>`;
}
function sjtHTML(q, e){
  const ans = (e.ans && e.ans[q.id]) || {}, show = e.practice;
  const items = q.items.map((it, i) => `<fieldset class="sjt-item"><legend>Scenario ${i + 1} of ${q.items.length}</legend><p>${esc(it.s)}</p>
    ${it.o.map((o, j) => `<label class="sjt-opt${show && ans[i] != null && o[1] === 2 ? " best" : ""}"><input type="radio" name="sj-${i}" value="${j}" ${ans[i] === j ? "checked" : ""}><span>${esc(o[0])}</span>${show && ans[i] != null ? `<span class="tag">${o[1] === 2 ? "best" : o[1] === 1 ? "partly" : "weak"}</span>` : ""}</label>`).join("")}
    ${show && ans[i] != null ? `<p class="sjt-why"><b>${esc(it.lp)}.</b> ${esc(it.why)}</p>` : ""}</fieldset>`).join("");
  return `<div class="sjt-page" id="sjt"><div class="inner">
    <div class="meta" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:13px;color:var(--text-2)"><span class="pill d-SJT">SJT</span><span>${esc(q.src)}</span></div>
    <h2 style="font-size:24px">${esc(q.title)}</h2>${q.body}
    ${items}
    <div class="sjt-foot"><span id="sjt-count" class="status">${sjtAnswered(q, ans)} of ${q.items.length} answered</span><div class="spacer" style="flex:1"></div><span class="status">${show ? "Practice: the best answer and the reason show after you pick." : "Answers save as you pick. Change them any time before the test ends."}</span></div>
  </div></div>`;
}
