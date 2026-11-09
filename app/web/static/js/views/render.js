"use strict";
// Top-level view switcher.

/* ---------- rendering ---------- */
let tick = null;
function render(){
  clearInterval(tick);
  cm = null; ta = null;
  const app = $("#app");
  if (S.view === "home") app.innerHTML = homeHTML(), bindHome();
  else if (S.view === "exam") app.innerHTML = examHTML(), bindExam();
  else app.innerHTML = reportHTML(), bindReport();
  window.scrollTo(0, 0);
}
