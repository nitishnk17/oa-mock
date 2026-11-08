// Home page: the companies on this computer and the ones you can download (see oa_mock/library.py).
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const H = { "Content-Type": "application/json", "X-Token": window.LOCAL_TOKEN };
  const VERB = { download: "downloading", update: "updating", remove: "removing", check: "checking for new questions" };
  let lib = null, polling = false, filter = "";

  const api = (path, body) => fetch(path, body ? { method: "POST", headers: H, body: JSON.stringify(body) } : { headers: H })
    .then((r) => r.json().then((j) => { if (!r.ok) throw new Error(j.error || r.statusText); return j; }));

  const mb = (b) => !b ? "" : b < 1e6 ? Math.max(1, Math.round(b / 1e3)) + " KB" : (b / 1e6).toFixed(b < 1e7 ? 1 : 0) + " MB";
  const busy = () => lib && lib.job && lib.job.state === "running";
  const hue = (k) => { let h = 0; for (const c of k) h = (h * 31 + c.charCodeAt(0)) % 360; return h; };
  const nameOf = (k) => { const c = lib && lib.companies.find((x) => x.key === k); return c ? c.name || k : k; };
  const short = (n) => String(n || "").replace(/\s*OA Mock$/i, "");

  function meta(c) {   // one line, coloured like code:  amazon/  10 questions · 2026, 2024 · SDE Intern
    const bits = ['<span class="k">' + esc(c.key) + "/</span>"];
    if (c.questions) bits.push('<span class="n">' + c.questions + "</span> question" + (c.questions === 1 ? "" : "s"));
    if (c.years && c.years.length) bits.push('<span class="n">' + esc(c.years.join(", ")) + "</span>");
    if (c.roles && c.roles.length) bits.push('<span class="s">' + esc(c.roles.slice(0, 3).join(" · ")) + "</span>");
    if (!c.installed && (c.download || c.bytes)) bits.push('<span class="c">' + mb(c.download || c.bytes) + "</span>");
    return bits.join('<span class="c">  ·  </span>');
  }

  function card(c) {
    const running = busy() && lib.job.company === c.key;
    const dis = busy() ? " disabled" : "";
    let acts = "", state = "";
    if (c.installed) {
      acts += '<a class="btn ghost" href="/' + esc(c.key) + '">open →</a>';
      if (c.update) acts += '<button class="btn" data-act="update" data-key="' + esc(c.key) + '"' + dis + ">get new questions</button>";
      if (lib.git.git && !c.onlyLocal) acts += '<button class="btn quiet danger" data-act="remove" data-key="' + esc(c.key) + '"' + dis +
        ' title="Delete its questions from this computer (download again any time). Your past submissions are kept.">remove</button>';
      state = c.update ? '<span class="state new">● new questions</span>' : c.onlyLocal ? '<span class="state">● only on this computer</span>' : '<span class="state ok">● ready</span>';
    } else {
      acts += '<button class="btn" data-act="download" data-key="' + esc(c.key) + '"' + dis + ">" + (running ? VERB[lib.job.kind] + "…" : "↓ download") + "</button>";
    }
    const title = esc(short(c.name) || c.key);
    const name = c.installed ? '<a class="name" href="/' + esc(c.key) + '">' + title + "</a>" : '<span class="name">' + title + "</span>";
    return '<div class="company panel' + (c.installed ? " mine" : "") + (running ? " running" : "") + '" style="--hue:' + hue(c.key) + '">' +
      '<div class="body"><div class="top">' + name + state + "</div>" + (c.tagline ? '<div class="tag">' + esc(c.tagline) + "</div>" : "") +
      '<div class="meta">' + meta(c) + "</div></div>" + '<div class="acts">' + acts + "</div></div>";
  }

  function matches(c) {
    if (!filter) return true;
    const hay = [c.key, c.name, c.tagline, (c.roles || []).join(" "), (c.years || []).join(" "), (c.colleges || []).join(" "), (c.formats || []).join(" ")].join(" ").toLowerCase();
    return filter.split(/\s+/).every((w) => hay.includes(w));
  }

  function status() {
    const st = lib.git, j = lib.job, el = $("status");
    let msg = "", cls = "status";
    if (j && j.state === "running") msg = "<span class=mono>" + VERB[j.kind] + (j.company ? " " + esc(short(nameOf(j.company))) : "") + "…</span>";
    else if (j && j.state === "failed") { msg = "That didn't work: " + esc(j.error); cls += " bad"; }
    else if (!st.git) msg = "Showing the companies in this folder. To download more, get the app with git (see the README). " + esc(st.why ? "(" + st.why + ")" : "");
    else if (!st.remote) msg = "This copy has no GitHub remote to download from.";
    else if (st.behind) { msg = "An update is available: " + st.behind + " new change" + (st.behind === 1 ? "" : "s") + ' on GitHub. <button class="btn" data-act="update">update</button>'; cls += " info"; }
    el.className = cls; el.innerHTML = msg; el.hidden = !msg;
    const log = $("joblog");
    log.hidden = !(j && j.log); log.querySelector("pre").textContent = (j && j.log) || "";
  }

  function checks() {
    const L = lib.langs || {}, mine = lib.companies.filter((c) => c.installed);
    const qs = mine.reduce((n, c) => n + (c.questions || 0), 0);
    const items = [
      ["", "<b>" + mine.length + "</b> compan" + (mine.length === 1 ? "y" : "ies") + " · <b>" + qs + "</b> questions here"],
      [L.cpp ? "" : "no", "C++17"], [L.java ? "" : "no", "Java"], ["", "Python"], ["", "JavaScript"],
    ];
    $("checks").innerHTML = items.map(([c, t]) => "<li" + (c ? ' class="' + c + '"' : "") + ">" + t + "</li>").join("");
  }

  function render() {
    const all = lib.companies.filter(matches);
    const mine = all.filter((c) => c.installed), avail = all.filter((c) => !c.installed);
    $("mine").innerHTML = mine.length ? mine.map(card).join("") : '<p class="empty">' + (filter ? "// nothing here matches" : "// no companies yet. download one below") + "</p>";
    $("avail").innerHTML = avail.map(card).join("");
    $("more").hidden = !avail.length;
    $("check").hidden = !(lib.git.git && lib.git.remote);
    $("check").disabled = busy();
    checks(); status();
  }

  function load() {
    return api("/api/library").then((j) => { lib = j; render(); if (busy()) poll(); })
      .catch((e) => { const s = $("status"); s.hidden = false; s.className = "status bad"; s.textContent = "Couldn't load the company list: " + e.message; });
  }

  function poll() {
    if (polling) return;
    polling = true;
    const tick = () => api("/api/library/job").then((j) => {
      lib.job = j;
      if (j.state === "running") { status(); setTimeout(tick, 700); return; }
      polling = false; load();
    }).catch(() => { polling = false; setTimeout(load, 1500); });
    tick();
  }

  function act(kind, key) {
    if (kind === "remove" && !confirm("Remove " + short(nameOf(key)) + " from this computer?\n\nYou can download it again any time. Your past submissions are kept.")) return;
    api("/api/library", { action: kind, company: key || null }).then((j) => { lib.job = j; render(); poll(); })
      .catch((e) => { lib.job = { state: "failed", error: e.message }; render(); });
  }

  document.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-act]");
    if (b && !b.disabled) act(b.dataset.act, b.dataset.key);
  });
  $("check").addEventListener("click", () => act("check"));
  $("q").addEventListener("input", (e) => { filter = e.target.value.trim().toLowerCase(); if (lib) render(); });
  $("q").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { const a = document.querySelector("#mine a.name"); if (a) location.href = a.href; }
    if (e.key === "Escape") { e.target.value = ""; filter = ""; render(); e.target.blur(); }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== $("q") && !e.ctrlKey && !e.metaKey) { e.preventDefault(); $("q").focus(); }
  });
  load();
})();
