// Home page: the companies on this computer and the ones you can download (see oa_mock/library.py).
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const H = { "Content-Type": "application/json", "X-Token": window.LOCAL_TOKEN };
  const VERB = { download: "Downloading", update: "Updating", remove: "Removing", check: "Checking for new questions" };
  let lib = null, polling = false, filter = "";

  const api = (path, body) => fetch(path, body ? { method: "POST", headers: H, body: JSON.stringify(body) } : { headers: H })
    .then((r) => r.json().then((j) => { if (!r.ok) throw new Error(j.error || r.statusText); return j; }));

  const mb = (b) => !b ? "" : b < 1e6 ? Math.max(1, Math.round(b / 1e3)) + " KB" : (b / 1e6).toFixed(b < 1e7 ? 1 : 0) + " MB";
  const busy = () => lib && lib.job && lib.job.state === "running";
  const short = (n) => String(n || "").replace(/\s*OA Mock$/i, "");
  const nameOf = (k) => { const c = lib && lib.companies.find((x) => x.key === k); return c ? short(c.name) || k : k; };
  const plural = (n, w) => n + " " + w + (n === 1 ? "" : "s");

  function monogram(c) {   // "Amazon" -> "Am", "Goldman Sachs" -> "GS"
    const words = short(c.name || c.key).split(/[\s-]+/).filter(Boolean);
    return words.length > 1 ? (words[0][0] + words[1][0]).toUpperCase() : (words[0] || c.key).slice(0, 2).replace(/^./, (x) => x.toUpperCase());
  }
  const logo = (c) => '<div class="logo" aria-hidden="true">' + (c.logo && /^data:image\/(svg\+xml|png|webp);base64,/.test(c.logo)
    ? '<img src="' + esc(c.logo) + '" alt="">' : '<span class="mono-gram">' + esc(monogram(c)) + "</span>") + "</div>";

  function meta(c) {
    const bits = [];
    if (c.questions) bits.push("<span><b>" + c.questions + "</b> question" + (c.questions === 1 ? "" : "s") + "</span>");
    if (c.years && c.years.length) bits.push("<span>" + esc(c.years.join(", ")) + "</span>");
    if (c.roles && c.roles.length) bits.push("<span>" + esc(c.roles.slice(0, 2).join(", ")) + (c.roles.length > 2 ? " +" + (c.roles.length - 2) : "") + "</span>");
    return bits.length ? '<div class="meta">' + bits.join("") + "</div>" : "";
  }

  function tile(c) {
    const running = busy() && lib.job.company === c.key;
    const dis = busy() ? " disabled" : "";
    const name = esc(short(c.name) || c.key);
    let state = "", acts = "";
    if (c.installed) {
      state = c.update ? '<span class="state new">New questions</span>' : c.onlyLocal ? '<span class="state">Only here</span>' : '<span class="state ready">Ready</span>';
      acts += '<a class="btn primary sm" href="/' + esc(c.key) + '">Open</a>';
      if (c.update) acts += '<button class="btn sm" data-act="update" data-key="' + esc(c.key) + '"' + dis + ">Get new questions</button>";
      acts += '<span class="sp"></span>';
      if (lib.git.git && !c.onlyLocal) acts += '<button class="btn quiet sm danger" data-act="remove" data-key="' + esc(c.key) + '"' + dis +
        ' title="Delete its questions from this computer. You can download it again; past submissions are kept.">Remove</button>';
    } else {
      acts += '<button class="btn sm" data-act="download" data-key="' + esc(c.key) + '"' + dis + ">" +
        (running ? VERB[lib.job.kind] + "…" : "Download" + (c.download || c.bytes ? ' <span class="k">' + mb(c.download || c.bytes) + "</span>" : "")) + "</button>";
    }
    return '<div class="tile ' + (c.installed ? "mine" : "avail") + (running ? " running" : "") + '">' +
      (c.installed ? '<a class="cover" href="/' + esc(c.key) + '" aria-label="Open ' + name + '"></a>' : "") +
      '<div class="tile-head">' + logo(c) + '<div><div class="tile-name">' + name + "</div>" + (c.tagline ? '<div class="tile-tag">' + esc(c.tagline) + "</div>" : "") + "</div>" + state + "</div>" +
      meta(c) + '<div class="tile-acts">' + acts + "</div></div>";
  }

  function matches(c) {
    if (!filter) return true;
    const hay = [c.key, c.name, c.tagline, (c.roles || []).join(" "), (c.years || []).join(" "), (c.colleges || []).join(" "), (c.formats || []).join(" ")].join(" ").toLowerCase();
    return filter.split(/\s+/).every((w) => hay.includes(w));
  }

  function status() {
    const st = lib.git, j = lib.job, el = $("status");
    let msg = "", cls = "notice";
    if (j && j.state === "running") msg = "<b>" + VERB[j.kind] + (j.company ? " " + esc(nameOf(j.company)) : "") + "…</b>";
    else if (j && j.state === "failed") { msg = "That didn't work: " + esc(j.error); cls += " bad"; }
    else if (!st.git) msg = "Showing the companies in this folder. To download more, install the app with git (see the README).";
    else if (!st.remote) msg = "This copy has no GitHub remote to download from.";
    else if (st.behind) { msg = "<b>An update is available.</b> " + plural(st.behind, "new change") + ' on GitHub.<span class="sp"></span><button class="btn primary sm" data-act="update">Update</button>'; cls += " info"; }
    el.className = cls; el.innerHTML = msg; el.hidden = !msg;
    const log = $("joblog");
    log.hidden = !(j && j.log); log.querySelector("pre").textContent = (j && j.log) || "";
  }

  function header() {
    const L = lib.langs || {}, mine = lib.companies.filter((c) => c.installed);
    const qs = mine.reduce((n, c) => n + (c.questions || 0), 0), years = new Set();
    mine.forEach((c) => (c.years || []).forEach((y) => years.add(y)));
    $("langs").innerHTML = [["C++17", L.cpp], ["Java", L.java], ["Python", true], ["JavaScript", true]]
      .map(([n, ok]) => "<li" + (ok ? "" : ' class="no" title="Not installed on this computer"') + ">" + n + "</li>").join("");
    const facts = [["Companies", mine.length], ["Questions", qs], ["Available", lib.companies.length - mine.length], ["Years", years.size ? Math.min(...years) + "–" + String(Math.max(...years)).slice(2) : "—"]];
    $("facts").innerHTML = facts.map(([k, v]) => "<div><dt>" + k + "</dt><dd>" + v + "</dd></div>").join("");
    $("facts").hidden = false;
  }

  function render() {
    const all = lib.companies.filter(matches);
    const mine = all.filter((c) => c.installed), avail = all.filter((c) => !c.installed);
    $("mine").innerHTML = mine.length ? mine.map(tile).join("") : '<p class="empty">' + (filter ? "No company matches “" + esc(filter) + "”." : "No companies yet. Download one below.") + "</p>";
    $("avail").innerHTML = avail.map(tile).join("");
    $("more").hidden = !avail.length;
    $("n-mine").textContent = mine.length ? String(mine.length) : "";
    $("n-avail").textContent = avail.length ? String(avail.length) : "";
    $("check").hidden = !(lib.git.git && lib.git.remote);
    $("check").disabled = busy();
    header(); status();
  }

  function load() {
    return api("/api/library").then((j) => { lib = j; render(); if (busy()) poll(); })
      .catch((e) => { const s = $("status"); s.hidden = false; s.className = "notice bad"; s.textContent = "Couldn't load the company list: " + e.message; });
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
    if (kind === "remove" && !confirm("Remove " + nameOf(key) + " from this computer?\n\nYou can download it again any time. Your past submissions are kept.")) return;
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
    if (e.key === "Enter") { const a = document.querySelector("#mine .tile .cover"); if (a) location.href = a.href; }
    if (e.key === "Escape") { e.target.value = ""; filter = ""; if (lib) render(); e.target.blur(); }
  });
  document.addEventListener("keydown", (e) => {
    const t = e.target;
    if (e.key === "/" && !/INPUT|TEXTAREA|SELECT/.test(t.tagName) && !e.ctrlKey && !e.metaKey) { e.preventDefault(); $("q").focus(); }
  });
  load();
})();
