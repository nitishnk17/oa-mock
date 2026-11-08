"use strict";
// Sends code to the local server (/run) and grades results against tests.

/* ---------- local runner (C++ / Java / CPython) ---------- */
async function serverRun(lang, code, inputs){
  const r = await fetch("/run", {method:"POST", headers:{"Content-Type":"application/json", "X-Token":window.LOCAL_TOKEN || ""}, body:JSON.stringify({lang, code, inputs, limit:LIMIT[lang]})});
  if (!r.ok) throw new Error("The local runner answered " + r.status + ". Restart oa_mock_local.py");
  return r.json();
}
async function runOne(lang, code, inp){
  if (NEEDS_LOCAL(lang)) throw new Error(LANGS[lang].label + " needs the local runner");
  if (LOCAL && lang !== "js"){ const resp = await serverRun(lang, code, [inp]); if (resp.compile_error != null) return {out:"", err:resp.compile_error, ms:0, ce:true}; return resp.results[0]; }
  return RUN[lang].run(code, inp, LIMIT[lang]);
}

/* ---------- server-side grading (C++, Java, Python) ---------- */
// The page doesn't carry hidden tests; the server runs them and sends back each result with a preview.
const serverGraded = (q, lang) => LOCAL && q.type === "code" && lang !== "js";
async function gradeOnServer(q, lang, code, full){
  const r = await fetch("/api/grade", {method:"POST", headers:{"Content-Type":"application/json", "X-Token":window.LOCAL_TOKEN || ""},
    body:JSON.stringify({company:window.OA_COMPANY, qid:q.id, lang, code, scope: full ? "all" : "samples"})});
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || "the local runner answered " + r.status);
  const n = full ? q.samples.length + (q.hiddenCount || 0) : q.samples.length;
  if (j.compile_error != null){
    const res = [{ok:false, kind:"Compilation error", err:j.compile_error, out:"", ms:0}];
    while (res.length < n) res.push({ok:false, kind:"Compilation error", err:"", out:"", ms:0});
    return {res, tests: res.map((_, i) => i < q.samples.length ? q.samples[i] : {in:"", out:""})};
  }
  const tests = j.results.map((x, i) => x.sample ? q.samples[i] : x.shown ? {in:x.in, out:x.expected} : {in:"", out:""});
  return {res: j.results, tests};
}
// Hidden tests for questions graded in the browser (JavaScript, SQL, the debugging repo), fetched once on Submit
async function hiddenOf(q){
  if (q._hidden) return q._hidden;
  const r = await fetch(`/api/companies/${encodeURIComponent(window.OA_COMPANY)}/questions/${encodeURIComponent(q.id)}/tests`);
  if (!r.ok) throw new Error("couldn't load the hidden tests (" + r.status + ")");
  q._hidden = (await r.json()).hidden;
  return q._hidden;
}

/* ---------- judge ---------- */
async function judge(q, lang, code, tests, onEach){
  const out = []; judge.batch = null;
  for (let i = 0; i < tests.length; i++){
    const t = tests[i]; let r;
    if (q.type === "sql"){
      const t0 = performance.now();
      try { const got = sqlRun(code, t); r = {ok:sameRows(got.rows, t.out), got, ms:performance.now() - t0}; }
      catch (e){ r = {ok:false, err:String(e && e.message || e), ms:performance.now() - t0}; }
      r.kind = r.err ? "Runtime error" : r.ok ? "Passed" : "Wrong answer";
    } else if (NEEDS_LOCAL(lang)) {
      throw new Error(LANGS[lang].label + " needs the local runner. Open this test through oa_mock_local.py on your laptop, or switch to Python");
    } else if (LOCAL && lang !== "js") {
      if (!judge.batch || judge.batch.code !== code || judge.batch.lang !== lang || judge.batch.tests !== tests){
        const resp = await serverRun(lang, code, tests.map(z => z.in));
        judge.batch = {code, lang, tests, resp};
      }
      const resp = judge.batch.resp;
      if (resp.compile_error != null) r = {ok:false, kind:"Compilation error", err:resp.compile_error, out:"", ms:0};
      else { const x = resp.results[i]; const ok = !x.tle && !x.err && cmpOut(q, x.out) === norm(t.out);
        r = {ok, out:x.out, err:x.err, ms:x.ms, kind: x.tle ? "Time limit exceeded" : x.err ? "Runtime error" : ok ? "Passed" : "Wrong answer"}; }
    } else {
      const x = await RUN[lang].run(code, t.in, LIMIT[lang]);
      const ok = !x.tle && !x.err && cmpOut(q, x.out) === norm(t.out);
      r = {ok, out:x.out, err:x.err, ms:x.ms, kind: x.tle ? "Time limit exceeded" : x.err ? "Runtime error" : ok ? "Passed" : "Wrong answer"};
    }
    out.push(r); if (onEach) onEach(i, r);
  }
  return out;
}
