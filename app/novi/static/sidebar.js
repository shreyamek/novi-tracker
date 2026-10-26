"use strict";
// Sidebar behaviour (ported from the Second Brain UI): icon rail on desktop, drawer with backdrop on phones,
// expandable sections, breadcrumb and clock. app.js builds the nav and calls window.NOVI_SHELL.
// Section and rail state is remembered in localStorage when that is available; the page works the same without it.
(function () {
  const LS = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private window or blocked storage: fine */ } },
  };
  const shell = document.querySelector(".shell");
  const toggle = document.getElementById("sidetoggle");
  const menu = document.getElementById("menu");
  const backdrop = document.getElementById("backdrop");
  const tabs = document.getElementById("tabs");
  const crumbEl = document.getElementById("crumb");
  const clock = document.getElementById("clock");
  const small = () => !!(window.matchMedia && window.matchMedia("(max-width: 820px)").matches);
  const isRail = () => shell.classList.contains("rail");
  const groups = () => Array.prototype.slice.call(tabs.querySelectorAll("details[data-grp]"));
  let before = {};

  // a section opens unless the person closed it last time; while the rail is on every section is open
  function restoreGroup(g) {
    g.open = isRail() ? true : LS.get("novi.grp." + g.dataset.grp) !== "0";
  }

  // remember open and closed sections (toggle does not bubble, so listen in the capture phase)
  tabs.addEventListener("toggle", (ev) => {
    const g = ev.target;
    if (g.matches && g.matches("details[data-grp]") && !isRail()) LS.set("novi.grp." + g.dataset.grp, g.open ? "1" : "0");
  }, true);

  function setRail(on, remember) {
    if (on === isRail()) return;
    if (on) {
      before = {};
      groups().forEach((g) => { before[g.dataset.grp] = g.open; g.open = true; });
    } else {
      groups().forEach((g) => { g.open = before[g.dataset.grp] !== undefined ? before[g.dataset.grp] : LS.get("novi.grp." + g.dataset.grp) !== "0"; });
    }
    shell.classList.toggle("rail", on);
    toggle.setAttribute("aria-expanded", String(!on));
    toggle.setAttribute("aria-label", on ? "Expand sidebar" : "Collapse sidebar");
    toggle.title = on ? "expand sidebar" : "collapse sidebar";
    if (remember) LS.set("novi.rail", on ? "1" : "0");
  }
  toggle.addEventListener("click", () => setRail(!isRail(), true));
  if (LS.get("novi.rail") === "1" && !small()) setRail(true, false);

  // drawer on small screens
  const closeDrawer = () => shell.classList.remove("drawer");
  menu.addEventListener("click", () => shell.classList.toggle("drawer"));
  backdrop.addEventListener("click", closeDrawer);
  tabs.addEventListener("click", (ev) => {
    if (small() && ev.target.closest && ev.target.closest("button[data-tab]")) closeDrawer();
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") closeDrawer();
    if ((ev.ctrlKey || ev.metaKey) && ev.key === "\\") {
      ev.preventDefault();
      if (small()) shell.classList.toggle("drawer"); else toggle.click();
    }
  });

  // footer clock
  const tick = () => { clock.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); };
  tick();
  setInterval(tick, 15000);

  window.NOVI_SHELL = {
    restoreGroup,
    setCrumb(text) { crumbEl.textContent = text; },
  };
})();
