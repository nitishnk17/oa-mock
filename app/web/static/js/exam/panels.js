"use strict";
// Resizable / collapsible editor panels.

/* ---------- resizable, collapsible panels ---------- */
const UI = Object.assign({left:46, ch:260, min:false}, store.get("oa-ui", {}));
const saveUI = () => store.set("oa-ui", UI);
function applyLeft(){ const ex = document.querySelector(".exam"); if (ex && innerWidth > 900) ex.style.gridTemplateColumns = `minmax(0,${UI.left}%) 8px minmax(0,1fr)`; else if (ex) ex.style.gridTemplateColumns = ""; }
function setConsole(min){
  UI.min = min; saveUI(); const c = $("#console"), t = $("#ctoggle"); if (!c) return;
  c.classList.toggle("min", min); t.setAttribute("aria-expanded", String(!min)); if (cm) cm.refresh();
}
function bindPanels(){
  applyLeft();
  const ex = document.querySelector(".exam"), work = document.querySelector(".work"), con = $("#console");
  const drag = (handle, onMove) => handle.addEventListener("pointerdown", ev => {
    if (innerWidth <= 900) return; ev.preventDefault(); handle.setPointerCapture(ev.pointerId); document.body.classList.add("dragging");
    const mv = e => onMove(e), up = () => { handle.removeEventListener("pointermove", mv); handle.removeEventListener("pointerup", up); document.body.classList.remove("dragging"); saveUI(); if (cm) cm.refresh(); };
    handle.addEventListener("pointermove", mv); handle.addEventListener("pointerup", up);
  });
  drag($("#rz-v"), e => { const r = ex.getBoundingClientRect(); UI.left = Math.min(70, Math.max(22, (e.clientX - r.left) / r.width * 100)); applyLeft(); });
  drag($("#rz-h"), e => { const r = work.getBoundingClientRect(); UI.ch = Math.round(Math.min(r.height - 140, Math.max(90, r.bottom - e.clientY))); con.style.height = UI.ch + "px"; if (UI.min) setConsole(false); });
  $("#rz-v").addEventListener("keydown", e => { if (e.key === "ArrowLeft" || e.key === "ArrowRight"){ UI.left = Math.min(70, Math.max(22, UI.left + (e.key === "ArrowLeft" ? -3 : 3))); applyLeft(); saveUI(); if (cm) cm.refresh(); } });
  $("#rz-h").addEventListener("keydown", e => { if (e.key === "ArrowUp" || e.key === "ArrowDown"){ UI.ch = Math.max(90, UI.ch + (e.key === "ArrowUp" ? 30 : -30)); con.style.height = UI.ch + "px"; if (UI.min) setConsole(false); saveUI(); if (cm) cm.refresh(); } });
  $("#ctoggle").addEventListener("click", () => setConsole(!UI.min));
}
function setStat(text, cls){ const s = $("#cstat"); if (s){ s.textContent = text; s.className = "cstat " + (cls || ""); } }
function missingHelp(lang){
  const n = OAInstall.NAME[lang], busy = OAInstall.installing(lang), what = lang === "cpp" ? "a C++ compiler" : "a Java JDK";
  return `<div class="missing-help"><div class="verdict warn">${busy ? `Installing ${n}…` : `${LANGS[lang].label} isn't installed on this computer`}</div>`
    + `<p style="margin:0 0 10px">${busy ? `When it finishes, Run and Submit work in ${n}. You can keep writing code meanwhile.` : `Run and Submit need ${what}. You can keep writing code; install it here, or switch to Python or JavaScript.`}</p>`
    + `<button class="btn ${busy ? "" : "primary"}" data-install="${lang}">${busy ? "Show progress" : `Install ${n}`}</button></div>`;
}
function localHelp(){
  return `<div class="verdict warn">C++ and Java run on your own computer</div><p style="margin:0 0 6px">A browser page can't compile C++, so this page only runs Python, JavaScript and SQL. To use C++ or Java, start OA Mock on your computer, in its folder:</p><pre class="tc" style="padding:8px 10px;margin:0 0 6px">./start.sh</pre><p class="muted" style="margin:0">On a Mac you can double-click <b>Start OA Mock.command</b>; on Windows, <b>start.bat</b>. If you ran setup, <code>oa-mock</code> works from any folder. It opens at http://127.0.0.1:8765 and compiles with your g++ (C++17) and javac. You can keep writing C++ here, but Run and Submit need the local runner.</p>`;
}
