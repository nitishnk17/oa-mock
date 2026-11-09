// "Add a question": paste an LLM's JSON, run the checks (app/server/contribute.py), save it, open a pull request.
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const H = { "Content-Type": "application/json", "X-Token": window.LOCAL_TOKEN };
  const api = (path, body) => fetch(path, body ? { method: "POST", headers: H, body: JSON.stringify(body) } : { headers: H })
    .then((r) => r.json().then((j) => { if (!r.ok) throw new Error(j.error || r.statusText); return j; }));
  const ICON = { ok: "✓", warn: "!", fail: "✗", skip: "–" };
  const LANG = { py: "Python", cpp: "C++", java: "Java", js: "JavaScript" };
  const DRAFT = "oa-contribute-draft";
  let status = null, last = null, saved = null;

  /* ---- step 1: the prompt ---- */
  let promptText = null;
  const getPrompt = () => promptText ? Promise.resolve(promptText) : fetch("/static/llm-prompt.md").then((r) => r.text()).then((t) => (promptText = t));
  $("copy").onclick = () => getPrompt().then((t) => navigator.clipboard.writeText(t)).then(() => { $("copied").hidden = false; setTimeout(() => ($("copied").hidden = true), 1800); })
    .catch(() => { $("show").click(); });
  $("show").onclick = () => getPrompt().then((t) => { const p = $("prompt"); p.textContent = t; p.hidden = !p.hidden; $("show").textContent = p.hidden ? "View it" : "Hide it"; });

  /* ---- step 2: company + JSON ---- */
  function companies() {
    const sel = $("company"), keep = sel.value;
    sel.innerHTML = status.companies.map((c) => '<option value="' + esc(c.key) + '">' + esc(c.name.replace(/\s*OA Mock$/i, "")) + "</option>").join("") +
      '<option value="__new">New company…</option>';
    if (keep) sel.value = keep;
    $("newco").hidden = sel.value !== "__new";
  }
  $("company").onchange = () => { $("newco").hidden = $("company").value !== "__new"; };
  $("cname").oninput = () => { if (!$("ckey").dataset.touched) $("ckey").value = $("cname").value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); };
  $("ckey").oninput = () => { $("ckey").dataset.touched = "1"; };
  const company = () => $("company").value === "__new" ? $("ckey").value.trim() : $("company").value;

  function parse(text) {   // LLMs wrap JSON in ``` fences and add notes after it: take the outermost {...}
    const a = text.indexOf("{"), b = text.lastIndexOf("}");
    if (a < 0 || b < a) throw new Error("no JSON object found");
    try { return JSON.parse(text.slice(a, b + 1)); }
    catch (e) { throw new Error("the JSON doesn't parse: " + e.message); }
  }
  try { $("json").value = localStorage.getItem(DRAFT) || ""; } catch (e) {}
  $("json").oninput = () => { try { localStorage.setItem(DRAFT, $("json").value); } catch (e) {} };
  const loadFile = (f) => f && f.text().then((t) => { $("json").value = t; $("json").oninput(); });
  $("file").onchange = (e) => loadFile(e.target.files[0]);
  const drop = $("drop");
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("over"));
  drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); loadFile(e.dataTransfer.files[0]); });

  /* ---- step 3: checks ---- */
  function showResults(res) {
    const n = (s) => res.checks.filter((c) => c.status === s).length;
    $("summary").innerHTML = '<span class="t-ok">' + n("ok") + " passed</span>" +
      '<span class="t-warn">' + n("warn") + " warning" + (n("warn") === 1 ? "" : "s") + "</span>" +
      '<span class="t-bad">' + n("fail") + " failed</span>";
    $("results").innerHTML = res.checks.map((c) => {
      const lines = (c.detail || "").split("\n");
      return '<details class="res ' + c.status + '"' + (c.status === "fail" ? " open" : "") + "><summary><span class=ic>" + ICON[c.status] + "</span>" +
        '<span class="nm">' + esc(c.name) + '</span><span class="first">' + esc(lines[0]) + "</span></summary>" +
        (c.detail ? "<pre>" + esc(c.detail) + "</pre>" : "") + "</details>";
    }).join("");
    const st = (res.question || {}).stub;
    $("preview").hidden = !st;
    if (st) {
      const langs = Object.keys(st);
      $("ptabs").innerHTML = '<span class="ptab-lbl">What solvers see</span>' +
        langs.map((l, i) => '<button data-l="' + l + '"' + (i ? "" : ' class="on"') + ">" + LANG[l] + "</button>").join("");
      $("pcode").textContent = st[langs[0]];
      $("ptabs").querySelectorAll("button").forEach((b) => (b.onclick = () => {
        $("ptabs").querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b)); $("pcode").textContent = st[b.dataset.l];
      }));
    }
    $("save").disabled = !res.ok;
    $("save").textContent = res.ok ? "Save to my bank" : "Fix the failed checks first";
  }

  function run() {
    let q;
    $("s3").hidden = false; $("saved").textContent = ""; $("s4").hidden = true; saved = null;
    try {
      q = parse($("json").value);
      if (!company()) throw new Error("pick a company (or type the new company's key)");
    } catch (e) {
      $("summary").textContent = ""; $("preview").hidden = true; $("save").disabled = true;
      $("results").innerHTML = '<details class="res fail" open><summary><span class=ic>✗</span><span class="nm">Read the JSON</span><span class="first">' + esc(e.message) + "</span></summary></details>";
      return;
    }
    $("results").innerHTML = '<div class="running-line"><span class="spin"></span>Running the checks: format, function spec, references, drivers in 4 languages, wrong answers, duplicates…</div>';
    $("summary").textContent = ""; $("save").disabled = true; $("run").disabled = true;
    last = { company: company(), question: q };
    api("/api/contribute/check", last).then(showResults)
      .catch((e) => { $("results").innerHTML = '<div class="res fail"><pre>' + esc(e.message) + "</pre></div>"; })
      .finally(() => { $("run").disabled = false; $("s3").scrollIntoView({ behavior: "smooth", block: "start" }); });
  }
  $("run").onclick = run;
  document.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); run(); } });

  $("save").onclick = () => {
    if (!last) return;
    $("save").disabled = true; $("saved").textContent = "saving…";
    api("/api/contribute/save", Object.assign({ name: $("cname").value, replace: false }, last)).then((r) => {
      saved = { company: last.company, qid: last.question.id };
      $("saved").innerHTML = '<span class="t-ok">Saved</span> ' + r.written.map((p) => "<code>" + esc(p) + "</code>").join(" ") +
        ' <a href="/' + esc(saved.company) + '">Try it</a>';
      try { localStorage.removeItem(DRAFT); } catch (e) {}
      share();
    }).catch((e) => { $("saved").innerHTML = '<span class="t-bad">' + esc(e.message) + "</span>"; $("save").disabled = false; });
  };

  /* ---- step 4: pull request ---- */
  function share() {
    $("s4").hidden = false;
    const s = status, el = $("share");
    const file = "data/" + saved.company + "/questions/" + saved.qid + ".json";
    const manual = "<p>Or by hand: fork the repository on GitHub, add <code>" + esc(file) + "</code>" +
      (s.companies.some((c) => c.key === saved.company) ? "" : " and <code>data/" + esc(saved.company) + "/company.json</code>") +
      ", run <code>python3 tools/build_catalog.py</code>, commit and open a pull request.</p>";
    if (!s.git) { el.innerHTML = "<p>This copy isn't a git clone, so it can't send pull requests. Your question is saved here and works in the app.</p>" + manual; return; }
    if (!s.gh) { el.innerHTML = '<p>Sending it from here needs the <a href="https://cli.github.com" target="_blank" rel="noopener">GitHub CLI</a> (<code>gh</code>). Install it, run <code>gh auth login</code> once, then reload this page.</p>' + manual; return; }
    if (!s.login) { el.innerHTML = "<p>The GitHub CLI isn't signed in. Run <code>gh auth login</code> in a terminal, then reload this page.</p>" + manual; return; }
    el.innerHTML = '<div class="share"><p>Signed in to GitHub as <b>' + esc(s.login) + "</b>. This opens a pull request to <code>" + esc(s.upstream) +
      "</code> with just this question" + (s.login.toLowerCase() === (s.upstream || "").split("/")[0].toLowerCase() ? "" : " (from your fork, which is created if you don't have one)") +
      ". Your files here stay as they are.</p><textarea id=note placeholder=\"Anything to tell the reviewer? Where it's from, what you had to assume…\"></textarea>" +
      '<div class="row"><button class="btn primary" id="pr">Open pull request</button><span id="prout" class="pr"></span></div></div>';
    $("pr").onclick = () => {
      $("pr").disabled = true; $("prout").textContent = "Pushing…";
      api("/api/contribute/share", { company: saved.company, qid: saved.qid, note: $("note").value })
        .then((r) => { $("prout").innerHTML = '<span class="t-ok">Opened</span> <a href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.url) + "</a>"; })
        .catch((e) => { $("prout").innerHTML = '<span class="t-bad">' + esc(e.message) + "</span>"; $("pr").disabled = false; });
    };
  }

  api("/api/contribute/status").then((s) => { status = s; companies(); })
    .catch((e) => { $("results").textContent = e.message; });
})();
