"use strict";
// Small helpers shared by every module.

/* ---------- helpers ---------- */
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const TRUNC_AT = 4000;
const trunc = s => { s = String(s); return s.length > TRUNC_AT ? s.slice(0, TRUNC_AT) + `\n… truncated, ${s.length - TRUNC_AT} more characters` : s; };
const $ = s => document.querySelector(s);
const norm = s => String(s).replace(/\r/g,"").split("\n").map(l => l.replace(/\s+$/,"")).join("\n").replace(/\n+$/,"").replace(/^\n+/,"");
const fmtTime = ms => { ms = Math.max(0, ms); const s = Math.floor(ms/1000), h = Math.floor(s/3600), m = Math.floor(s%3600/60), x = s%60; return (h ? h+":" : "") + String(m).padStart(2,"0") + ":" + String(x).padStart(2,"0"); };
const pick = a => a[Math.floor(Math.random()*a.length)];
const byDiff = d => QS.filter(q => q.diff === d);
const ORDER = {Easy:0, Medium:1, Hard:2, SQL:3, Debug:4, SJT:5};
// Bank order: newest year first (questions without a year last), then difficulty, then title.
const bankSort = (a, b) => (b.year || 0) - (a.year || 0) || (b.month || 0) - (a.month || 0) || ORDER[a.diff] - ORDER[b.diff] || a.title.localeCompare(b.title);
const bankIds = () => [...QS].sort(bankSort).map(q => q.id);
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const qTags = q => [q.month ? MONTHS[q.month - 1] + " " + q.year : q.year, q.role, q.college].filter(Boolean);
const touched = (e, id) => !!(e.best[id] || (e.ans && e.ans[id] && Object.keys(e.ans[id]).length) || Object.entries(e.code[id] || {}).some(([l, c]) => c !== starterOf(QMAP[id], l)));
/* ---------- problem style: LeetCode (edit a function; a hidden driver does the I/O) or HackerRank (edit the whole program) ---------- */
let STYLE = store.get("oa-style", "leetcode");
const hasDriver = (q, lang) => !!(q && q.driver && q.driver[lang]);
const isHR = (q, lang) => STYLE === "hackerrank" && hasDriver(q, lang);
const bufKey = (q, lang) => isHR(q, lang) ? lang + "@hr" : lang;           // each style keeps its own code
const stubOf = (q, lang) => (q && q.stub && q.stub[lang] != null) ? q.stub[lang] : (q && q.starter != null) ? q.starter : STARTER[lang];
const fullProgram = (q, lang, fnCode) => q.driver[lang].pre + fnCode + q.driver[lang].post;
// starter for a buffer key: "py" -> the function stub, "py@hr" -> the full program around it
const starterOf = (q, key) => key.endsWith("@hr") ? fullProgram(q, key.slice(0, -3), stubOf(q, key.slice(0, -3))) : stubOf(q, key);
const srcOf = (q, code, lang) => q.type === "debug" ? q.pre + "\n" + code + "\n" + q.post : hasDriver(q, lang) && !isHR(q, lang) ? fullProgram(q, lang, code) : code;
function setStyle(v){
  if (v === STYLE) return;
  if (typeof saveCode === "function") saveCode();       // keep the buffer you were editing
  STYLE = v; store.set("oa-style", v);
  if (typeof render === "function") render();
}
const cmpOut = (q, out) => norm(q.type === "debug" ? String(out).split("\n").filter(l => !l.startsWith("[log]")).join("\n") : out);
const sjtMax = q => q.items.length * 2;
const sjtScore = (q, ans) => { const a = ans || {}; let p = 0; q.items.forEach((it, i) => { if (a[i] != null) p += it.o[a[i]][1]; }); return p; };
const sjtAnswered = (q, ans) => Object.keys(ans || {}).length;

/* ---------- light / dark switch for the top bars (theme.js does the work) ---------- */
const THEME_BTN = `<button class="icon-btn theme-btn" data-theme-toggle aria-label="Dark mode" aria-pressed="false"><svg class="i-moon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13.5 9.6A5.6 5.6 0 0 1 6.4 2.5a5.6 5.6 0 1 0 7.1 7.1Z"/></svg><svg class="i-sun" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="8" cy="8" r="3"/><path d="M8 1.5v1.3M8 13.2v1.3M1.5 8h1.3M13.2 8h1.3M3.4 3.4l.9.9M11.7 11.7l.9.9M3.4 12.6l.9-.9M11.7 4.3l.9-.9"/></svg></button>`;
