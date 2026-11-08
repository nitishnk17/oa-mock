"use strict";
// Past submissions: saved by the local server in .oa-cache/submissions/ (see oa_mock/submissions.py).

const COMPANY = window.OA_COMPANY;   // URL key of this company, e.g. "amazon"

const SUBS = {
  async api(method, path, body){
    const headers = {"X-Token": window.LOCAL_TOKEN || ""};
    if (body) headers["Content-Type"] = "application/json";
    const r = await fetch(path, {method, headers, body: body ? JSON.stringify(body) : undefined});
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.error || "the server answered " + r.status);
    return j;
  },
  save(sub){ return this.api("POST", "/api/submissions", Object.assign({company: COMPANY}, sub)); },
  list(qid, limit){ return this.api("GET", `/api/submissions?company=${encodeURIComponent(COMPANY)}${qid ? "&qid=" + encodeURIComponent(qid) : ""}&limit=${limit || 200}`); },
  get(qid, sid){ return this.api("GET", `/api/submissions/${encodeURIComponent(COMPANY)}/${encodeURIComponent(qid)}/${encodeURIComponent(sid)}`); },
  remove(qid, sid){ return this.api("DELETE", `/api/submissions/${encodeURIComponent(COMPANY)}/${encodeURIComponent(qid)}/${encodeURIComponent(sid)}`); },
};

// Called after every Submit. Never blocks grading: a failed save only shows a note.
function recordSubmission(q, lang, code, score, passed, total, e){
  if (q.type === "sjt") return;
  SUBS.save({qid: q.id, title: q.title, lang, code, score, passed, total, practice: e.practice, style: isHR(q, lang) ? "hackerrank" : "leetcode",
             format: e.practice ? "Practice" : (FORMATS[e.fmt] ? FORMATS[e.fmt].name : e.fmt)})
    .then(() => { const b = $("#subs-btn"); if (b) b.classList.add("pulse"); setTimeout(() => b && b.classList.remove("pulse"), 1200); })
    .catch(err => toast("Couldn't save this submission: " + err.message));
}
