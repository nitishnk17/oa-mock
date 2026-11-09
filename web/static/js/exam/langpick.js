"use strict";
// The language menu in the editor toolbar. A button and a small popover instead of a <select>, so a language
// this computer can't run yet can carry a download icon that installs it (see install.js).

const langMissing = l => LOCAL && !!window.OAInstall && OAInstall.missing(l);
const langNote = l => !langMissing(l) ? "" : OAInstall.installing(l) ? "Installing…" : "Not installed";

function langButtonInner(cur){
  return `<span class="lp-cur">${LANGS[cur].label}</span>${langMissing(cur) ? `<span class="lp-flag">${esc(langNote(cur))}</span>` : ""}`;
}
function langPickerHTML(langs, cur, title){
  return `<span class="lp" id="lp" data-langs="${langs.join(",")}"><button class="lp-btn${langMissing(cur) ? " missing" : ""}" id="lang" value="${cur}" aria-haspopup="true" aria-expanded="false" title="${esc(title)}">`
    + langButtonInner(cur) + `</button></span>`;
}
function langMenuHTML(langs, cur){
  return `<div class="lp-pop" id="lp-pop" role="dialog" aria-label="Language">${langs.map(l => `<div class="lp-row">`
    + `<button class="lp-opt" data-v="${l}" aria-pressed="${l === cur}"><span class="lp-check" aria-hidden="true">${l === cur ? "✓" : ""}</span><span class="lp-name">${LANGS[l].label}</span>`
    + `${langNote(l) ? `<span class="lp-note">${langNote(l)}</span>` : ""}</button>${LOCAL && window.OAInstall ? OAInstall.button(l) : ""}</div>`).join("")}</div>`;
}
function closeLangMenu(refocus){
  const p = $("#lp-pop"); if (!p) return;
  p.remove(); const b = $("#lang"); if (b){ b.setAttribute("aria-expanded", "false"); if (refocus) b.focus(); }
}
// The menu sets #lang's value and fires "change" on it, like the <select> it replaced.
function bindLangPicker(){
  const btn = $("#lang"), wrap = $("#lp"); if (!btn || !wrap) return;
  const langs = wrap.dataset.langs.split(",");
  const pick = v => { closeLangMenu(true); if (v === btn.value) return; btn.value = v; btn.dispatchEvent(new Event("change", {bubbles: true})); };
  const openMenu = () => {
    btn.insertAdjacentHTML("afterend", langMenuHTML(langs, btn.value)); btn.setAttribute("aria-expanded", "true");
    const pop = $("#lp-pop");
    (pop.querySelector('.lp-opt[aria-pressed="true"]') || pop.querySelector(".lp-opt")).focus();
    pop.addEventListener("click", e => {
      e.stopPropagation();
      if (e.target.closest("[data-install]")) return closeLangMenu(false);   // install.js opens its dialog
      const o = e.target.closest(".lp-opt"); if (o) pick(o.dataset.v);
    });
    pop.addEventListener("keydown", e => {
      const items = [...pop.querySelectorAll(".lp-opt")], i = items.indexOf(document.activeElement);
      if (e.key === "Escape"){ e.preventDefault(); e.stopPropagation(); closeLangMenu(true); }
      else if (e.key === "ArrowDown" || e.key === "ArrowUp"){ e.preventDefault(); const row = document.activeElement.closest(".lp-row"), r = [...pop.querySelectorAll(".lp-row")].indexOf(row);
        const n = items[(Math.max(r, 0) + (e.key === "ArrowDown" ? 1 : items.length - 1)) % items.length]; if (n) n.focus(); }
      else if (e.key === "ArrowRight" && i >= 0){ const d = items[i].parentNode.querySelector("[data-install]"); if (d){ e.preventDefault(); d.focus(); } }
      else if (e.key === "ArrowLeft" && document.activeElement.matches("[data-install]")){ e.preventDefault(); document.activeElement.parentNode.querySelector(".lp-opt").focus(); }
      else if (e.key === "Home" || e.key === "End"){ e.preventDefault(); items[e.key === "Home" ? 0 : items.length - 1].focus(); }
      else if (e.key === "Tab") closeLangMenu(false);
    });
    setTimeout(() => document.addEventListener("click", function close(){ closeLangMenu(false); document.removeEventListener("click", close); }), 0);
  };
  btn.addEventListener("click", ev => { ev.stopPropagation(); $("#lp-pop") ? closeLangMenu(true) : openMenu(); });
  btn.addEventListener("keydown", ev => { if ((ev.key === "ArrowDown" || ev.key === "ArrowUp") && !$("#lp-pop")){ ev.preventDefault(); openMenu(); } });
}

// A language finished installing (or started): refresh what shows it, without re-rendering the editor.
function refreshLangUI(){
  if (S.view === "home"){ const sel = $("#lang0"); if (sel) [...sel.options].forEach(o => { o.textContent = LANGS[o.value].label + (langMissing(o.value) ? " (not installed)" : ""); }); return; }
  if (S.view !== "exam" || !S.exam) return;
  const wrap = $("#lp"), e = S.exam, id = e.ids[e.cur], q = QMAP[id], lang = e.lang[id];
  if (!wrap || !q || q.type === "sjt") return;
  const btn = $("#lang");   // updated in place: controls.js listens for "change" on this element
  btn.classList.toggle("missing", langMissing(btn.value)); btn.innerHTML = langButtonInner(btn.value);
  const pop = $("#lp-pop");
  if (pop){ const f = document.activeElement, v = f && f.dataset ? (f.dataset.v || f.dataset.install) : null, wasDl = f && f.matches && f.matches("[data-install]");
    closeLangMenu(false); btn.click();
    const back = v && $(wasDl ? `#lp-pop [data-install="${v}"]` : `#lp-pop .lp-opt[data-v="${v}"]`); if (back) back.focus(); }
  const rt = $("#rt"); if (rt) rt.textContent = runtimeNote(q, lang);
  const out = $("#out"); if (out && out.querySelector(".missing-help")) out.innerHTML = langMissing(lang) ? missingHelp(lang) : `<p class="muted">Run your code to see the results here.</p>`;
}
if (window.OAInstall) OAInstall.onChange(() => refreshLangUI());
