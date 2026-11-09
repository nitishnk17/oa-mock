"use strict";
// Timer, question navigation, Run / Submit and results.

function bindTimer(e){
  if (e.practice) return;
  const t = () => {
    const el = $("#timer"); if (!el) return;
    if (e.untimed){ const v = $("#tval"); if (v) v.textContent = fmtTime(Date.now() - e.start); return; }
    const left = e.start + e.dur - Date.now(); el.textContent = fmtTime(left); el.classList.toggle("low", left < 5*60000); if (left <= 0) endExam(true);
  };
  t(); tick = setInterval(t, 1000);
}
function goQ(e, i){ if (i < 0 || i >= e.ids.length || i === e.cur) return; saveCode(); e.cur = i; saveExam(); render(); }
function bindNav(e){
  document.querySelectorAll(".qtab").forEach(b => b.addEventListener("click", () => goQ(e, +b.dataset.q)));
  const qp = $("#qpick"); if (qp) qp.addEventListener("change", () => goQ(e, +qp.value));
  $("#prev").addEventListener("click", () => goQ(e, e.cur - 1));
  $("#next").addEventListener("click", () => goQ(e, e.cur + 1));
  $("#nav-home").addEventListener("click", () => { saveCode(); saveExam(); S.view = "home"; render(); });
  $("#end").addEventListener("click", () => e.practice ? endExam(false) : confirmEnd());
}
function bindSjt(e, q){
  bindNav(e);
  const fit = () => { const pg = $("#sjt"), bar = document.querySelector(".bar"); if (pg && bar) pg.style.height = (innerHeight - bar.getBoundingClientRect().bottom) + "px"; };
  window.onresize = fit; setTimeout(fit, 0);
  document.querySelectorAll('#sjt input[type="radio"]').forEach(r => r.addEventListener("change", () => {
    const i = +r.name.slice(3); e.ans = e.ans || {}; e.ans[q.id] = e.ans[q.id] || {}; e.ans[q.id][i] = +r.value;
    const pts = sjtScore(q, e.ans[q.id]), na = sjtAnswered(q, e.ans[q.id]);
    e.best[q.id] = {score:Math.round(pts / sjtMax(q) * 100), passed:pts, total:sjtMax(q), lang:"sjt", at:Date.now()};
    saveExam();
    const c = $("#sjt-count"); if (c) c.textContent = `${na} of ${q.items.length} answered`;
    const tab = document.querySelector(`.qtab[data-q="${e.cur}"] .dot`); if (tab) tab.className = "dot " + (na === q.items.length ? "full" : "part");
    if (e.practice){ const y = $("#sjt").scrollTop; render(); const pg = $("#sjt"); if (pg) pg.scrollTop = y; }
  }));
  bindTimer(e);
}
function bindExam(){
  const e = S.exam, id = e.ids[e.cur], q = QMAP[id];
  if (q.type === "sjt") return bindSjt(e, q);
  const fit = () => { const ex = document.querySelector(".exam"), bar = document.querySelector(".bar"); if (ex && bar && innerWidth > 900) ex.style.height = (innerHeight - bar.getBoundingClientRect().bottom) + "px"; else if (ex) ex.style.height = ""; if (cm) cm.refresh(); };
  window.onresize = fit; setTimeout(fit, 0);
  bindPanels();
  $("#subs-btn").addEventListener("click", () => openSubmissions(id));
  bindEditorSettings();
  const kh = $("#keys-help"); if (kh) kh.addEventListener("click", showShortcuts);
  mountEditor($("#editor"), codeOf(id, e.lang[id]), e.lang[id]);
  bindNav(e);
  bindLangPicker();
  $("#lang").addEventListener("change", ev => { saveCode(); e.lang[id] = ev.target.value; if (q.type === "code") { S.lang = ev.target.value; store.set(K + "-lang", S.lang); } saveExam(); render(); });
  $("#reset").addEventListener("click", () => { const v = starterOf(q, bufKey(q, e.lang[id])); if (cm) cm.setValue(v); else if (ta) ta.value = v; saveCode(); });
  $("#run").addEventListener("click", () => doRun(false));
  $("#submit").addEventListener("click", () => doRun(true));
  const uc = $("#usecustom"); if (uc) uc.addEventListener("change", () => { $("#custom").hidden = !uc.checked; if (uc.checked && !$("#custom").value) $("#custom").value = q.samples[0].in; });
  bindTimer(e);
}

let busy = false;
async function doRun(full){
  if (busy || !S.exam || S.exam.ended) return;
  saveCode();
  const e = S.exam, id = e.ids[e.cur], q = QMAP[id], lang = e.lang[id];
  if (q.type === "sjt") return;
  if (langMissing(lang)){ $("#out").innerHTML = missingHelp(lang); if (UI.min) setConsole(false); setStat(LANGS[lang].label + " isn't installed", "bad"); return; }
  const code = srcOf(q, codeOf(id, lang), lang);
  const out = $("#out"), runB = $("#run"), subB = $("#submit");
  busy = true; runB.disabled = subB.disabled = true;
  if (UI.min) setConsole(false);
  setStat(full ? "Submitting…" : "Running…", "");
  const custom = !full && $("#usecustom") && $("#usecustom").checked;
  try {
    if (custom){
      out.innerHTML = `<p class="muted">Running on custom input…</p>`;
      const r = await runOne(lang, code, $("#custom").value);
      out.innerHTML = `<div class="verdict ${r.tle || r.err ? "bad" : "ok"}">${r.tle ? "Time limit exceeded" : r.ce ? "Compilation error" : r.err ? "Runtime error" : "Finished"}<span class="status">${Math.round(r.ms)} ms</span></div>
        <div class="tc"><div class="body"><div><div class="lbl">Your output</div><pre>${esc(trunc(r.out || "(nothing printed)"))}</pre></div>${r.err ? `<div><div class="lbl">Error</div><pre class="err">${esc(trunc(r.err))}</pre></div>` : ""}</div></div>`;
      setStat(r.tle ? "Time limit exceeded" : r.ce ? "Compilation error" : r.err ? "Runtime error" : "Custom run finished", r.tle || r.err ? "bad" : "ok");
      return;
    }
    let tests, res;
    if (serverGraded(q, lang)){
      const n = full ? q.samples.length + (q.hiddenCount || 0) : q.samples.length;
      out.innerHTML = `<p class="muted" id="prog">Running ${n} test case${n === 1 ? "" : "s"} on your computer…</p>`;
      ({tests, res} = await gradeOnServer(q, lang, code, full));
    } else {
      if (full) out.innerHTML = `<p class="muted" id="prog">Loading the hidden tests…</p>`;
      tests = full ? [...q.samples, ...(await hiddenOf(q))] : q.samples;
      out.innerHTML = `<p class="muted" id="prog">Running… 0/${tests.length}</p>`;
      res = await judge(q, lang, code, tests, i => { const p = $("#prog"); if (p) p.textContent = `Running… ${i + 1}/${tests.length}`; });
    }
    const passed = res.filter(r => r.ok).length, score = Math.round(passed / tests.length * 100);
    if (full){
      const prev = e.best[id];
      if (!prev || score >= prev.score) e.best[id] = {score, passed, total:tests.length, lang, at:Date.now()};
      saveExam();
      const tab = document.querySelector(`.qtab[data-q="${e.cur}"] .dot`); if (tab) tab.className = "dot " + (score === 100 ? "full" : score > 0 ? "part" : "");
      if (res[0].kind !== "Compilation error") recordSubmission(q, lang, codeOf(id, lang), score, passed, tests.length, e);
    }
    const ns = q.samples.length;
    const verdict = passed === tests.length ? ["ok", full ? "All test cases passed" : "Sample cases passed"] : passed ? ["warn", `${passed}/${tests.length} test cases passed`] : ["bad", res[0].kind === "Time limit exceeded" ? "Time limit exceeded" : res[0].kind === "Compilation error" ? "Compilation error" : res.some(r => r.err) ? "Runtime error" : "Wrong answer"];
    let html = `<div class="verdict ${verdict[0]}">${verdict[1]}${full ? `<span class="status">Score ${score}/100 · best ${e.best[id].score}/100</span>` : ""}</div>`;
    // Hidden cases stay hidden: pass/fail only, plus the first one that fails (to inspect, rerun or download).
    const firstBad = full ? res.findIndex((r, i) => i >= ns && !r.ok) : -1;
    const shown = i => i < ns || i === firstBad;
    const name = i => i < ns ? "S" + i : "T" + (i - ns + 1);
    if (full) html += `<div class="grid-tests" aria-label="Test results">${res.map((r, i) => `<span class="res ${r.ok ? "ok" : r.kind.startsWith("Time") ? "warn" : "bad"}"${shown(i) ? ` title="Show case ${name(i)}" data-tc="${i}" tabindex="0" role="button"` : ` title="Hidden case ${name(i)}"`}>${name(i)} ${r.ok ? "✓" : "✗"}</span>`).join("")}</div><p class="status" style="margin-top:8px">S = sample, T = hidden. Hidden cases only show pass/fail${firstBad >= 0 ? `; the first one that failed (${name(firstBad)}) is shown below` : ""}.</p>`;
    if (res[0].kind === "Compilation error") html += `<pre class="err" style="white-space:pre-wrap">${esc(res[0].err)}</pre>`;
    else html += res.map((r, i) => shown(i) ? tcHTML(q, tests[i], r, i, i < ns ? "Sample case " + i : "Hidden case " + name(i), i === firstBad) : "").join("");
    out.innerHTML = html;
    out.querySelectorAll("[data-tc]").forEach(el => {
      const jump = () => { const d = $("#tc-" + el.dataset.tc); if (!d) return; d.open = true; d.scrollIntoView({behavior:"smooth", block:"center"}); };
      el.addEventListener("click", jump);
      el.addEventListener("keydown", ev => { if (ev.key === "Enter" || ev.key === " "){ ev.preventDefault(); jump(); } });
    });
    if (firstBad >= 0) wireHiddenCase(tests[firstBad], name(firstBad));
    setStat(full ? `${passed}/${tests.length} passed · ${score}/100` : `${passed}/${tests.length} samples passed`, verdict[0]);
  } catch (err){
    setStat("Error", "bad");
    out.innerHTML = `<div class="verdict bad">Could not run the code</div><p>${esc(err.message)}. ${lang === "py" ? "Python loads from the internet the first time; check your connection and press Run again." : ""}</p>`;
  } finally { busy = false; runB.disabled = subB.disabled = false; }
}
function tcHTML(q, t, r, i, label, tools){
  const cls = r.ok ? "ok" : r.kind.startsWith("Time") ? "warn" : "bad";
  let body;
  if (q.type === "sql"){
    body = `<div style="grid-column:1/-1">${r.err ? `<pre class="err">${esc(trunc(r.err))}</pre>` : tableHTML("your result", r.got.cols.length ? r.got.cols : ["(no columns)"], r.got.rows)}${tableHTML("expected", ["company_name", "department_name", "average_salary"], t.out)}</div>`;
  } else {
    body = `<div><div class="lbl">Input</div><pre>${esc(trunc(t.in))}</pre></div><div><div class="lbl">Expected</div><pre>${esc(trunc(t.out))}</pre></div><div><div class="lbl">Your output</div><pre>${esc(trunc(r.out || "(nothing printed)"))}</pre></div>${r.err ? `<div style="grid-column:1/-1"><div class="lbl">Error</div><pre class="err">${esc(trunc(r.err))}</pre></div>` : ""}`;
  }
  const extra = tools && q.type !== "sql" ? `<div class="tc-tools">${$("#usecustom") ? `<button class="btn" data-hc="custom">Use as custom input</button>` : ""}<button class="btn" data-hc="in">Download input (.txt)</button><button class="btn" data-hc="out">Download expected output (.txt)</button><span class="status">input: ${t.in.length < 1024 ? t.in.length + " characters" : (t.in.length / 1024).toFixed(t.in.length < 10240 ? 1 : 0) + " KB"}</span></div>` : "";
  return `<details class="tc" id="tc-${i}" ${r.ok ? "" : "open"}><summary><span class="res ${cls}">${r.kind}</span>${label}<span class="ms">${Math.round(r.ms || 0)} ms</span></summary><div class="body">${body}</div>${extra}</details>`;
}
// Buttons on the first failing hidden case
function wireHiddenCase(t, name){
  const qid = S.exam.ids[S.exam.cur];
  const save = (text, file) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], {type:"text/plain"}));
    a.download = file; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  };
  document.querySelectorAll("[data-hc]").forEach(b => b.addEventListener("click", ev => {
    ev.preventDefault();
    const k = b.dataset.hc;
    if (k === "in") return save(t.in, `${qid}-${name}-input.txt`);
    if (k === "out") return save(t.out, `${qid}-${name}-expected.txt`);
    const uc = $("#usecustom"), box = $("#custom");
    uc.checked = true; box.hidden = false; box.value = t.in;
    box.scrollIntoView({behavior:"smooth", block:"center"});
    toast(`Case ${name} is in the custom input. Press Run to try it.`);
  }));
}

function confirmEnd(){
  const e = S.exam, done = e.ids.filter(id => e.best[id]).length;
  const m = $("#modal");
  m.innerHTML = `<div class="box" role="dialog" aria-modal="true" aria-labelledby="m-t"><h3 id="m-t" style="font-size:20px">End the test now?</h3><p class="muted" style="margin:0">You have submitted ${done} of ${e.ids.length} questions. Only submitted code counts towards the score.</p><div class="row"><button class="btn" id="m-no">Keep working</button><button class="btn primary" id="m-yes">End test</button></div></div>`;
  m.hidden = false; $("#m-no").focus();
  $("#m-no").onclick = closeModal; $("#m-yes").onclick = () => endExam(false);
}
function closeModal(){ const m = $("#modal"); m.hidden = true; m.innerHTML = ""; }
