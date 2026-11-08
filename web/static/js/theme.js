// Light / dark switch shared by the home and "Add a question" pages (remembered in this browser).
(function () {
  var KEY = "oa-theme", root = document.documentElement;
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function apply(t) { if (t) root.setAttribute("data-theme", t); else root.removeAttribute("data-theme"); }
  var saved = get();
  apply(saved || (window.matchMedia && matchMedia("(prefers-color-scheme: light)").matches ? "light" : null));
  window.toggleTheme = function () {
    var t = root.getAttribute("data-theme") === "light" ? "dark" : "light";
    apply(t === "dark" ? null : t);
    try { localStorage.setItem(KEY, t); } catch (e) {}
    var b = document.getElementById("theme"); if (b) b.textContent = t === "light" ? "☾" : "☀";
  };
  document.addEventListener("DOMContentLoaded", function () {
    var b = document.getElementById("theme");
    if (b) { b.textContent = root.getAttribute("data-theme") === "light" ? "☾" : "☀"; b.addEventListener("click", window.toggleTheme); }
  });
})();
