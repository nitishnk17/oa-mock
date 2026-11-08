// Home page: lists the companies on this computer and the ones you can download (see oa_mock/library.py).
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const H = { "Content-Type": "application/json", "X-Token": window.LOCAL_TOKEN };
  const VERB = { download: "Downloading", update: "Updating", remove: "Removing", check: "Checking for new questions" };
  let lib = null, polling = false;

  const api = (path, body) => fetch(path, body ? { method: "POST", headers: H, body: JSON.stringify(body) } : { headers: H })
    .then((r) => r.json().then((j) => { if (!r.ok) throw new Error(j.error || r.statusText); return j; }));

  const mb = (b) => !b ? "" : b < 1e6 ? Math.max(1, Math.round(b / 1e3)) + " KB" : (b / 1e6).toFixed(b < 1e7 ? 1 : 0) + " MB";
  const busy = () => lib && lib.job && lib.job.state === "running";

  function meta(c) {
    const bits = [];
    if (c.questions) bits.push(c.questions + " question" + (c.questions === 1 ? "" : "s"));
    if (c.years && c.years.length) bits.push(c.years.join(", "));
    if (c.roles && c.roles.length) bits.push(c.roles.slice(0, 3).join(" · "));
    return bits.map((b) => "<span>" + esc(b) + "</span>").join("");
  }

  function card(c) {
    const running = busy() && lib.job.company === c.key;
    const dis = busy() ? " disabled" : "";
    let acts = "";
    if (c.installed) {
      if (c.update) acts += '<button data-act="update" data-key="' + esc(c.key) + '"' + dis + ">Get new questions</button>";
      if (lib.git.git && !c.onlyLocal) acts += '<button class="ghost danger" data-act="remove" data-key="' + esc(c.key) + '"' + dis + ' title="Delete its questions from this computer (download again any time). Your past submissions are kept.">Remove</button>';
    } else {
      acts += '<button data-act="download" data-key="' + esc(c.key) + '"' + dis + ">" + (running ? VERB[lib.job.kind] + "…" : "Download" + (c.download || c.bytes ? " · " + mb(c.download || c.bytes) : "")) + "</button>";
    }
    const title = esc(c.name || c.key), tag = c.tagline ? "<small>" + esc(c.tagline) + "</small>" : "";
    const name = c.installed ? '<a class="name" href="/' + esc(c.key) + '">' + title + "</a>" : '<span class="name">' + title + "</span>";
    const badge = c.update ? '<span class="badge">New questions</span>' : c.onlyLocal ? '<span class="badge muted">Only on this computer</span>' : "";
    return '<div class="company' + (c.installed ? " mine" : "") + (running ? " running" : "") + '">' +
      '<div class="body">' + name + badge + tag + '<div class="meta">' + meta(c) + "</div></div>" +
      '<div class="acts">' + (c.installed ? '<a class="open" href="/' + esc(c.key) + '">Open</a>' : "") + acts + "</div></div>";
  }

  function status() {
    const st = lib.git, j = lib.job, el = $("status");
    let msg = "", cls = "status";
    if (j && j.state === "running") msg = VERB[j.kind] + (j.company ? " " + esc(nameOf(j.company)) : "") + "…";
    else if (j && j.state === "failed") { msg = "That didn't work: " + esc(j.error); cls += " bad"; }
    else if (!st.git) msg = "Showing the companies in this folder. To download more, get the app with git: see the README. (" + esc(st.why) + ")";
    else if (!st.remote) msg = "This copy has no GitHub remote to download from.";
    else if (st.behind) { msg = "An update is available (" + st.behind + " new change" + (st.behind === 1 ? "" : "s") + ' on GitHub). <button data-act="update">Update</button>'; cls += " info"; }
    el.className = cls; el.innerHTML = msg; el.hidden = !msg;
    const log = $("joblog");
    log.hidden = !(j && j.log); log.querySelector("pre").textContent = (j && j.log) || "";
  }

  const nameOf = (k) => { const c = lib.companies.find((x) => x.key === k); return c ? c.name || k : k; };

  function render() {
    const mine = lib.companies.filter((c) => c.installed), avail = lib.companies.filter((c) => !c.installed);
    $("mine").innerHTML = mine.length ? mine.map(card).join("") : '<p class="hint">No companies yet. Download one below.</p>';
    $("avail").innerHTML = avail.map(card).join("");
    $("more").hidden = !avail.length;
    $("check").hidden = !(lib.git.git && lib.git.remote);
    $("check").disabled = busy();
    status();
  }

  function load() {
    return api("/api/library").then((j) => { lib = j; render(); if (busy()) poll(); })
      .catch((e) => { $("status").hidden = false; $("status").className = "status bad"; $("status").textContent = "Couldn't load the company list: " + e.message; });
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
  load();
})();
