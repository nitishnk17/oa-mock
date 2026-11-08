"use strict";
// Past submissions: the list dialog, the code viewer, and the home-page panel.

const relTime = ms => {
  const s = (Date.now() - ms) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return Math.floor(s / 60) + " min ago";
  if (s < 86400) return Math.floor(s / 3600) + " h ago";
  if (s < 86400 * 7) return Math.floor(s / 86400) + " d ago";
  return new Date(ms).toLocaleDateString([], {day: "numeric", month: "short", year: "numeric"});
};
const whenHTML = ms => `<span title="${esc(new Date(ms).toLocaleString())}">${relTime(ms)}</span>`;
const scoreCls = s => s === 100 ? "ok" : s > 0 ? "warn" : "bad";
const langLabel = l => LANGS[l] ? LANGS[l].label : l;

function subsRowsHTML(list, withTitle){
  if (!list.length) return `<p class="muted" style="margin:6px 0">Nothing submitted yet. Every time you press <b>Submit code</b> it's saved here.</p>`;
  return `<div class="scroll-x"><table class="hist subs"><thead><tr><th>When</th>${withTitle ? "<th>Question</th>" : ""}<th>Language</th><th>Score</th><th>Tests</th><th>Mode</th><th></th></tr></thead><tbody>
    ${list.map(m => `<tr><td>${whenHTML(m.at)}</td>${withTitle ? `<td>${esc(QMAP[m.qid] ? QMAP[m.qid].title : m.title)}</td>` : ""}<td>${esc(langLabel(m.lang))}</td>
      <td><span class="res ${scoreCls(m.score)}">${m.score}/100</span></td><td class="n">${m.passed}/${m.total}</td><td>${esc(m.format || m.mode)}</td>
      <td><button class="btn sm" data-sub="${esc(m.qid)}|${esc(m.id)}">View</button></td></tr>`).join("")}</tbody></table></div>`;
}

// List for the question you're on (from the editor toolbar)
async function openSubmissions(qid){
  const m = $("#modal"), q = QMAP[qid];
  m.innerHTML = `<div class="box wide" role="dialog" aria-modal="true" aria-labelledby="m-t"><h3 id="m-t" style="font-size:20px">Past submissions · ${esc(q.title)}</h3><div id="subs-list"><p class="muted">Loading…</p></div>
    <div class="row"><button class="btn primary" id="m-no">Close</button></div></div>`;
  m.hidden = false; $("#m-no").onclick = closeModal;
  try {
    const list = await SUBS.list(qid);
    $("#subs-list").innerHTML = subsRowsHTML(list, false) + (list.length ? `<p class="status" style="margin:8px 0 0">Saved on this computer in <code>.oa-cache/submissions/${esc(COMPANY)}/${esc(qid)}/</code></p>` : "");
    bindSubRows($("#subs-list"), () => openSubmissions(qid));
  } catch (err){ $("#subs-list").innerHTML = `<p class="verdict bad">Couldn't load submissions: ${esc(err.message)}</p>`; }
}

function bindSubRows(root, back){
  root.querySelectorAll("[data-sub]").forEach(b => b.addEventListener("click", () => { const [qid, sid] = b.dataset.sub.split("|"); viewSubmission(qid, sid, back); }));
}

// Read-only view of one submission, with Load / Copy / Delete
async function viewSubmission(qid, sid, back){
  const m = $("#modal");
  let hit;
  try { hit = await SUBS.get(qid, sid); } catch (err){ toast("Couldn't open it: " + err.message); return; }
  const meta = hit.meta, q = QMAP[qid];
  const inExam = S.view === "exam" && S.exam && !S.exam.ended && S.exam.ids[S.exam.cur] === qid;
  const canLoad = q && (q.type === "sql" ? meta.lang === "sql" : q.type === "debug" ? meta.lang === "js" : CODE_LANGS.includes(meta.lang));
  m.innerHTML = `<div class="box wide" role="dialog" aria-modal="true" aria-labelledby="m-t">
    <h3 id="m-t" style="font-size:20px">${esc(q ? q.title : meta.title)}</h3>
    <div class="kpis" style="margin:0"><span>${whenHTML(meta.at)}</span><span><b>${esc(langLabel(meta.lang))}</b></span><span class="res ${scoreCls(meta.score)}">${meta.score}/100</span><span>${meta.passed}/${meta.total} tests</span><span>${esc(meta.format || meta.mode)}</span>${meta.style ? `<span>${meta.style === "hackerrank" ? "HackerRank style" : "LeetCode style"}</span>` : ""}</div>
    <div id="sub-code" class="sub-code"></div>
    <p class="status" style="margin:0">File: <code>${esc(meta.path)}</code></p>
    <div class="row" style="justify-content:space-between">
      <div style="display:flex;gap:8px;flex-wrap:wrap">${back ? `<button class="btn" id="sv-back">◀ All submissions</button>` : ""}<button class="btn danger" id="sv-del">Delete</button></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn" id="sv-copy">Copy</button>
        ${canLoad ? `<button class="btn primary" id="sv-load">${inExam ? "Load into editor" : "Practise with this code"}</button>` : ""}<button class="btn" id="m-no">Close</button></div>
    </div></div>`;
  m.hidden = false;
  const host = $("#sub-code");
  if (window.CodeMirror){
    const v = CodeMirror(host, {value: hit.code, mode: LANGS[meta.lang] ? LANGS[meta.lang].mode : "text/plain", readOnly: true, lineNumbers: true, tabSize: 4});
    setTimeout(() => v.refresh(), 0);
  } else host.innerHTML = `<pre>${esc(hit.code)}</pre>`;
  $("#m-no").onclick = closeModal;
  if (back) $("#sv-back").onclick = back;
  $("#sv-copy").onclick = () => navigator.clipboard.writeText(hit.code).then(() => toast("Copied"), () => toast("Copy failed: select the code and press " + MOD + "+C"));
  $("#sv-del").onclick = async () => {
    if ($("#sv-del").dataset.sure !== "1"){ $("#sv-del").dataset.sure = "1"; $("#sv-del").textContent = "Click again to delete"; return; }
    try { await SUBS.remove(qid, sid); toast("Deleted"); if (back) back(); else { closeModal(); render(); } } catch (err){ toast("Couldn't delete: " + err.message); }
  };
  if (canLoad) $("#sv-load").onclick = () => loadSubmission(qid, meta.lang, hit.code, meta.style);
}

function loadSubmission(qid, lang, code, style){
  closeModal();
  const ids = bankIds();
  const here = S.view === "exam" && S.exam && !S.exam.ended && S.exam.ids[S.exam.cur] === qid;
  const go = () => {
    if (!here){
      const e = S.exam;
      if (!(e && !e.ended && e.practice && e.ids.join() === ids.join())) startExam("practice", ids, 0, true, false, ids.indexOf(qid));
      else { e.cur = ids.indexOf(qid); }
    }
    const e = S.exam, id = e.ids[e.cur];
    saveCode();
    if (style && style !== STYLE){ STYLE = style; store.set("oa-style", style); }   // open it in the style it was written in
    e.lang[id] = lang; e.code[id] = e.code[id] || {}; e.code[id][bufKey(QMAP[id], lang)] = code;
    saveExam(); S.view = "exam"; render(); toast("Loaded your " + langLabel(lang) + " submission");
  };
  here ? go() : guardStart(go);
}

// Home page: most recent submissions for this company
function homeSubsHTML(){
  return `<section class="panel" aria-labelledby="h-subs"><h2 id="h-subs">Past submissions</h2><div id="home-subs"><p class="muted">Loading…</p></div></section>`;
}
async function fillHomeSubs(){
  const box = $("#home-subs"); if (!box) return;
  try {
    const all = await SUBS.list(null, 500);
    const shown = all.slice(0, 12);
    box.innerHTML = subsRowsHTML(shown, true) + (all.length > shown.length ? `<p class="status" style="margin:8px 0 0">Showing the latest ${shown.length} of ${all.length}. Each question's full list is under <b>🕘 Submissions</b> in the editor.</p>` : "")
      + (all.length ? `<p class="status" style="margin:6px 0 0">Files: <code>.oa-cache/submissions/${esc(COMPANY)}/</code></p>` : "");
    bindSubRows(box, null);
  } catch (err){ box.innerHTML = `<p class="muted">Past submissions aren't available: ${esc(err.message)}</p>`; }
}
