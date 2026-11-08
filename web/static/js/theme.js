// Light / dark, shared by every page and remembered in this browser. Light is the default.
// Loaded in <head> so the page never flashes the wrong theme.
(function () {
  var KEY = "oa-theme", root = document.documentElement;
  function saved() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function apply(t) {
    if (t === "dark") root.setAttribute("data-theme", "dark"); else root.removeAttribute("data-theme");
    var bs = document.querySelectorAll("[data-theme-toggle]");
    for (var i = 0; i < bs.length; i++) {
      bs[i].setAttribute("aria-pressed", t === "dark" ? "true" : "false");
      bs[i].title = t === "dark" ? "Switch to light" : "Switch to dark";
    }
  }
  window.getTheme = function () { return root.getAttribute("data-theme") === "dark" ? "dark" : "light"; };
  window.setTheme = function (t) {
    // switch instantly: no button or card should animate its colours to the new theme
    root.classList.add("theme-switching");
    apply(t);
    void root.offsetHeight;
    setTimeout(function () { root.classList.remove("theme-switching"); }, 50);
    try { localStorage.setItem(KEY, t); } catch (e) {}
    try { window.dispatchEvent(new CustomEvent("oa-theme", { detail: t })); } catch (e) {}
  };
  window.toggleTheme = function () { window.setTheme(window.getTheme() === "dark" ? "light" : "dark"); };
  apply(saved() === "dark" ? "dark" : "light");
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("[data-theme-toggle]");
    if (b) { e.preventDefault(); window.toggleTheme(); }
  });
  document.addEventListener("DOMContentLoaded", function () { apply(window.getTheme()); });
})();
