"use strict";
// Runs JavaScript answers in a Web Worker (the browser side of the judge).

/* ---------- JavaScript runner (Web Worker) ---------- */
const JS_WORKER = `
onmessage = async e => {
  const {id, src, inp} = e.data; let out = "", err = "";
  const handlers = {}, rlh = {};
  const show = x => typeof x === "string" ? x : (x && typeof x === "object" ? JSON.stringify(x) : String(x));
  const fmt = a => a.map(show).join(" ");
  const con = {log:(...a)=>{out += fmt(a) + "\\n"}, info:(...a)=>{out += fmt(a) + "\\n"}, error:(...a)=>{err += fmt(a) + "\\n"}, warn:()=>{}};
  const EXIT = {exit:true};
  const proc = {stdin:{on(ev, cb){handlers[ev] = cb; return this}, resume(){}, setEncoding(){}}, stdout:{write(s){out += String(s); return true}}, env:{}, argv:[], exit(){throw EXIT}};
  const rl = {createInterface(){ const o = {on(ev, cb){rlh[ev] = cb; return o}, close(){}}; return o; }};
  const req = n => { if (n === "fs") return {readFileSync: () => inp}; if (n === "readline") return rl; throw new Error("Module '" + n + "' is not available here"); };
  const t = performance.now();
  try {
    const ret = new Function("require", "process", "console", src)(req, proc, con);
    if (ret && typeof ret.then === "function") await ret;
    if (handlers.data) handlers.data(inp);
    if (handlers.end) handlers.end();
    if (rlh.line) for (const l of inp.replace(/\\n$/, "").split("\\n")) rlh.line(l);
    if (rlh.close) rlh.close();
  } catch (x) { if (x !== EXIT) err += (x && x.stack ? String(x.stack).split("\\n").slice(0, 3).join("\\n") : String(x)); }
  postMessage({id, out, err, ms: performance.now() - t});
};`;
class Runner {
  constructor(src){ this.src = src; this.w = null; this.ready = null; }
  boot(){
    if (this.ready) return this.ready;
    this.w = new Worker(URL.createObjectURL(new Blob([this.src], {type:"text/javascript"})));
    this.ready = new Promise((res, rej) => {
      if (this.src === JS_WORKER) return res();
      this.w.onmessage = e => e.data.ready ? res() : e.data.fatal ? rej(new Error(e.data.fatal)) : 0;
      this.w.onerror = ev => { ev.preventDefault(); rej(new Error(ev.message || "worker failed")); };
    }).catch(err => { this.kill(); throw err; });
    return this.ready;
  }
  kill(){ if (this.w) this.w.terminate(); this.w = null; this.ready = null; }
  async run(code, inp, limit){
    await this.boot();
    return new Promise(res => {
      const id = Math.random();
      const timer = setTimeout(() => { this.kill(); res({tle:true, out:"", err:"", ms:limit}); }, limit);
      this.w.onmessage = e => { if (e.data.id !== id) return; clearTimeout(timer); res(e.data); };
      this.w.onerror = ev => { ev.preventDefault(); clearTimeout(timer); this.kill(); res({out:"", err:String(ev.message || "crashed"), ms:0}); };
      this.w.postMessage({id, src:code, inp});
    });
  }
}
const RUN = {js:new Runner(JS_WORKER)};
