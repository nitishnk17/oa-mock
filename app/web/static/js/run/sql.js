"use strict";
// In-browser SQL engine (AlaSQL) for SQL questions.

/* ---------- SQL ---------- */
function sqlRun(query, test){
  if (typeof alasql === "undefined") throw new Error("The SQL engine did not load. Check your connection and reload.");
  const db = new alasql.Database();
  for (const [t, {cols, rows}] of Object.entries(test.tables)){
    db.exec(`CREATE TABLE ${t} (${cols.join(", ")})`);
    db.tables[t].data = rows.map(r => Object.fromEntries(cols.map((c, i) => [c, r[i]])));
  }
  let res = db.exec(query);
  if (Array.isArray(res) && res.length && Array.isArray(res[0])) res = res[res.length - 1];
  if (!Array.isArray(res)) res = [];
  return {cols: res.length ? Object.keys(res[0]) : [], rows: res.map(o => Object.values(o))};
}
const canonRow = r => r.map(v => typeof v === "number" ? (Math.round(v * 1000) / 1000).toFixed(3) : String(v)).join("\u0001");
const sameRows = (a, b) => { const x = a.map(canonRow).sort(), y = b.map(canonRow).sort(); return x.length === y.length && x.every((v, i) => v === y[i]); };
