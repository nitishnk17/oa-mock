// Installing C++ or Java from the app (see oa_mock/toolchain.py). Shared by the home page and the test app.
//   OAInstall.missing(lang)     true when this computer can't run that language yet
//   OAInstall.installing(lang)  true while its install runs
//   OAInstall.button(lang)      the download icon for a missing language ("" otherwise); a click opens the dialog
//   OAInstall.open(lang)        the dialog: confirm, progress with the setup script's log, then the result
//   OAInstall.onChange(fn)      fn(tools, event) after every change; event is {type: "done"|"failed", lang} when an install ends
// The password is never typed into this page: the setup script asks for it in the operating system's own dialog.
(function () {
  "use strict";
  const NAME = { cpp: "C++", java: "Java" };
  const H = { "Content-Type": "application/json", "X-Token": window.LOCAL_TOKEN };
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const ICON = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 2.5v7.5M4.8 7 8 10.2 11.2 7M3 13.2h10"/></svg>';
  const SPIN = '<span class="oi-spin" aria-hidden="true"></span>';
  let tools = window.OA_TOOLS || null, polling = false, dlg = null, dlgLang = null;
  const listeners = [];

  const api = (body) => fetch("/api/toolchain", body ? { method: "POST", headers: H, body: JSON.stringify(body) } : { headers: H })
    .then((r) => r.json().then((j) => { if (!r.ok) throw new Error(j.error || r.statusText); return j; }));

  const job = () => (tools && tools.job) || {};
  const running = () => job().state === "running";
  const info = (l) => tools && tools.langs && tools.langs[l];
  const missing = (l) => !!(info(l) && !info(l).ok);
  const installing = (l) => running() && job().lang === l;

  function emit(ev) { listeners.forEach((fn) => { try { fn(tools, ev); } catch (e) { console.error(e); } }); }

  function refresh() {
    return api().then((t) => { tools = t; emit(); if (running()) poll(); return t; });
  }

  function poll() {
    if (polling) return;
    polling = true;
    const tick = () => api().then((t) => {
      const was = job();
      tools = t;
      if (running()) { emit(); if (dlg && dlg.open && dlgLang === t.job.lang) drawProgress(); setTimeout(tick, 1000); return; }
      polling = false;
      const ev = t.job.id && t.job.id === was.id && t.job.state !== "running" ? { type: t.job.state, lang: t.job.lang } : null;
      emit(ev);
      if (dlg && dlg.open && dlgLang === t.job.lang) drawResult();
      else if (ev) toast(ev.type === "done" ? NAME[ev.lang] + " is installed. Run and Submit work now." : NAME[ev.lang] + " didn't install: " + (t.job.error || "see the details"),
                         ev.type === "failed" ? ev.lang : null);
    }).catch(() => setTimeout(tick, 2000));
    tick();
  }

  function button(l, extra) {
    if (!missing(l)) return "";
    const busy = installing(l), n = NAME[l];
    return '<button type="button" class="oi-btn' + (busy ? " busy" : "") + (extra ? " " + extra : "") + '" data-install="' + l + '" aria-label="'
      + (busy ? "Installing " + n + ", show progress" : "Install " + n) + '" title="' + (busy ? "Installing " + n + "…" : n + " isn't installed. Install it") + '">'
      + (busy ? SPIN : ICON) + "</button>";
  }

  /* ---------- the dialog ---------- */
  function dialog() {
    if (dlg) return dlg;
    dlg = document.createElement("dialog");
    dlg.className = "oi-dlg";
    dlg.setAttribute("aria-labelledby", "oi-t");
    dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });   // click outside the box
    dlg.addEventListener("close", () => { const back = document.querySelector('[data-install="' + dlgLang + '"]') || document.getElementById("lang"); if (back) back.focus(); });
    document.body.appendChild(dlg);
    return dlg;
  }
  function show(html, focus) {
    const d = dialog();
    d.innerHTML = '<div class="oi-box">' + html + "</div>";
    d.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => d.close()));
    if (!d.open) d.showModal();
    const f = focus && d.querySelector(focus); if (f) f.focus();
  }
  const logHTML = (opened) => job().log ? '<details class="oi-log"' + (opened ? " open" : "") + '><summary>Details</summary><pre>' + esc(job().log) + "</pre></details>" : "";

  function open(l) {
    if (!NAME[l]) return;
    dlgLang = l;
    if (installing(l)) return drawProgress(true);
    const t = info(l);
    if (!t || t.ok) return show('<h3 id="oi-t">' + NAME[l] + ' is installed</h3><p class="oi-muted">' + esc((t && t.desc) || "") + '</p><div class="oi-row"><button class="btn primary" data-close>Close</button></div>', "[data-close]");
    const p = t.plan || {};
    if (!p.can) {
      show('<h3 id="oi-t">Install ' + NAME[l] + ' from a terminal</h3><p>' + esc(p.why || "This computer can't install it from the app.") + "</p>"
        + '<pre class="oi-cmd">' + esc(p.terminal || "") + '</pre><div class="oi-row"><button class="btn" id="oi-copy">Copy command</button><button class="btn primary" data-close>Close</button></div>', "#oi-copy");
      bindCopy(p.terminal);
      return;
    }
    if (running()) {
      return show('<h3 id="oi-t">One install at a time</h3><p>' + NAME[job().lang] + " is still installing. Try " + NAME[l] + ' when it finishes.</p><div class="oi-row"><button class="btn primary" data-close>OK</button></div>', "[data-close]");
    }
    show('<h3 id="oi-t">Install ' + NAME[l] + " on this computer?</h3>"
      + "<p>This installs <b>" + esc(p.what || NAME[l]) + "</b> so " + NAME[l] + " answers can run and be graded here.</p>"
      + '<p class="oi-note">' + esc(p.auth || "") + "</p>"
      + '<p class="oi-muted">It runs <code>' + esc(p.terminal) + "</code> in the background. You can keep working while it runs.</p>"
      + '<div class="oi-row"><button class="btn" data-close>Not now</button><button class="btn primary" id="oi-go">Install ' + NAME[l] + "</button></div>", "#oi-go");
    dlg.querySelector("#oi-go").addEventListener("click", (e) => {
      e.target.disabled = true; e.target.textContent = "Starting…";
      api({ action: "install", lang: l }).then((j) => { tools.job = j; emit(); drawProgress(true); poll(); })
        .catch((err) => { tools.job = { state: "failed", lang: l, error: err.message }; drawResult(); });
    });
  }
  function bindCopy(text) {
    const b = dlg.querySelector("#oi-copy");
    b.addEventListener("click", () => {
      (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(() => { b.textContent = "Copied"; })
        .catch(() => { const r = document.createRange(); r.selectNodeContents(dlg.querySelector(".oi-cmd")); getSelection().removeAllRanges(); getSelection().addRange(r); });
    });
  }
  function drawProgress(focus) {
    const j = job(), d = dialog(), pre = d.open && d.querySelector("#oi-stop") && d.querySelector(".oi-log pre");
    if (pre) {   // already showing: update the log only, keeping its scroll position and the focus
      const atEnd = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 4;
      pre.textContent = j.log || ""; if (atEnd) pre.scrollTop = pre.scrollHeight;
      return;
    }
    show('<h3 id="oi-t">' + SPIN + " Installing " + NAME[j.lang] + "…</h3>"
      + '<p class="oi-note">' + esc(j.auth || "") + "</p>"
      + '<p class="oi-muted">You can hide this and keep working. A message shows when it finishes.</p>'
      + '<details class="oi-log"><summary>Details</summary><pre>' + esc(j.log || "") + "</pre></details>"
      + '<div class="oi-row"><button class="btn danger" id="oi-stop">Stop</button><button class="btn primary" data-close>Hide</button></div>', focus ? "[data-close]" : null);
    d.querySelector("#oi-stop").addEventListener("click", (e) => { e.target.disabled = true; api({ action: "cancel" }).catch(() => {}); });
  }
  function drawResult() {
    const j = job(), n = NAME[j.lang] || "It";
    if (j.state === "done") {
      show('<h3 id="oi-t" class="oi-ok">' + n + " is installed</h3><p>" + esc(j.desc || "") + "</p><p class=\"oi-muted\">Run and Submit work in " + n + " now.</p>"
        + logHTML(false) + '<div class="oi-row"><button class="btn primary" data-close>Done</button></div>', "[data-close]");
    } else {
      const p = (info(j.lang) || {}).plan || {};
      show('<h3 id="oi-t">' + n + " didn't install</h3><p>" + esc(j.error || "") + "</p>"
        + (p.terminal ? '<p class="oi-muted">You can also run this in a terminal, in the app\'s folder:</p><pre class="oi-cmd">' + esc(p.terminal) + "</pre>" : "")
        + logHTML(true) + '<div class="oi-row"><button class="btn" data-close>Close</button><button class="btn primary" id="oi-again">Try again</button></div>', "#oi-again");
      dlg.querySelector("#oi-again").addEventListener("click", () => open(j.lang));
    }
  }

  /* ---------- a message when an install ends with the dialog closed ---------- */
  function toast(msg, failedLang) {
    let t = document.getElementById("oi-toast");
    if (!t) { t = document.createElement("div"); t.id = "oi-toast"; t.className = "oi-toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
    t.innerHTML = esc(msg) + (failedLang ? ' <button class="oi-link" data-install-result="' + failedLang + '">Details</button>' : "");
    t.classList.add("show"); clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("show"), failedLang ? 9000 : 4000);
  }

  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-install]");
    if (b) { e.preventDefault(); open(b.dataset.install); return; }   // capture phase, no stopPropagation: menus see the click and close
    const r = e.target.closest("[data-install-result]");
    if (r) { dlgLang = r.dataset.installResult; document.getElementById("oi-toast").classList.remove("show"); drawResult(); }
  }, true);

  window.OAInstall = {
    get tools() { return tools; }, NAME, missing, installing, button, open, refresh,
    onChange(fn) { listeners.push(fn); },
  };
  if (tools && running()) poll();
})();
