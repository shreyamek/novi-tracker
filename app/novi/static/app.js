/* Novi app shell: builds the nav from /api/features and hands each tab a container to render into.
   Helpers on window.NOVI: h (safe element builder), api (JSON fetch), toast (short message), tabs (feature registry).
   Feature tabs register window.NOVI.tabs[name] = { render(container) } from their own script.
   The sidebar behaviour lives in sidebar.js (window.NOVI_SHELL), which loads first. */
(function () {
  "use strict";

  var LAST_TAB_KEY = "novi.lastTab";
  var HOME = "home";
  var HOME_ICON = "M3.5 9 10 3.5 16.5 9M5.5 8v8h9V8";
  var FALLBACK_ICON = "M4 5h12M4 10h12M4 15h8";
  var SVG_NS = "http://www.w3.org/2000/svg";

  // Build an element. Children are text or nodes only; profile or tracker text is never parsed as HTML.
  function h(tag, attrs) {
    var el = document.createElement(tag);
    var children = Array.prototype.slice.call(arguments, 2);
    Object.keys(attrs || {}).forEach(function (key) {
      var value = attrs[key];
      if (value === null || value === undefined || value === false) return;
      if (key === "class") el.className = value;
      else if (key.indexOf("on") === 0 && typeof value === "function") el.addEventListener(key.slice(2), value);
      else if (value === true) el.setAttribute(key, "");
      else el.setAttribute(key, String(value));
    });
    (function append(list) {
      list.forEach(function (child) {
        if (child === null || child === undefined || child === false) return;
        if (Array.isArray(child)) append(child);
        else if (child instanceof Node) el.appendChild(child);
        else el.appendChild(document.createTextNode(String(child)));
      });
    })(children);
    return el;
  }

  // Line icon from one SVG path d (built with createElementNS, never from markup strings).
  function icon(d) {
    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 20 20");
    svg.setAttribute("width", "18");
    svg.setAttribute("height", "18");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.6");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    var path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", typeof d === "string" && d ? d : FALLBACK_ICON);
    svg.appendChild(path);
    return svg;
  }

  // GET when body is undefined, otherwise POST JSON. Throws Error(message) with the server's message.
  function api(path, body) {
    var options = { method: body === undefined ? "GET" : "POST", headers: {} };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    return fetch(path, options).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) throw new Error(data.error || ("Request failed (" + res.status + ")"));
        return data;
      });
    });
  }

  var toastTimer = null;
  function toast(message) {
    var el = document.getElementById("toast");
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove("show"); }, 2600);
  }

  window.NOVI = { h: h, api: api, toast: toast, tabs: {} };

  var nav = document.getElementById("tabs");
  var main = document.getElementById("main");
  var features = [];
  var loadedAssets = {};

  function readLastTab() {
    try { return localStorage.getItem(LAST_TAB_KEY) || HOME; } catch (e) { return HOME; }
  }
  function saveLastTab(name) {
    try { localStorage.setItem(LAST_TAB_KEY, name); } catch (e) { /* private window or blocked storage: fine */ }
  }

  function loadStyle(href) {
    if (loadedAssets[href]) return;
    loadedAssets[href] = true;
    document.head.appendChild(h("link", { rel: "stylesheet", href: href }));
  }

  function loadScript(src) {
    if (loadedAssets[src]) return loadedAssets[src];
    loadedAssets[src] = new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("Could not load " + src)); };
      document.body.appendChild(s);
    });
    return loadedAssets[src];
  }

  function labelOf(f) { return (f.tab && f.tab.label) || f.name; }
  function groupOf(f) { return f.group || null; }
  function findFeature(name) {
    return features.filter(function (f) { return f.name === name; })[0] || null;
  }
  function crumb(text) { if (window.NOVI_SHELL) window.NOVI_SHELL.setCrumb(text); }

  // ---- home ----------------------------------------------------------------

  function stat(value, label) {
    return h("div", { class: "stat" }, h("b", null, String(value)), h("span", null, label));
  }

  function dateLabel() {
    return new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
  }

  // With a profile: the same summary numbers as Today, from the tracker and today feature when they are there.
  function homeSummary(container) {
    var tracker = api("/api/tracker").catch(function () { return null; });
    var today = api("/api/today").catch(function () { return null; });
    Promise.all([tracker, today]).then(function (parts) {
      var tr = parts[0], td = parts[1];
      var roles = (tr && tr.roles) || [];
      var count = function (s) { return roles.filter(function (r) { return r.status === s; }).length; };
      var stats = [];
      if (tr) {
        stats.push(stat(roles.length, "roles tracked"), stat(count("Applied"), "applied"),
          stat(count("Interviewing"), "interviewing"), stat(count("Offer"), "offers"));
      }
      if (td) {
        var todos = td.todos || [], habits = td.habits || [], ticks = td.ticks || [];
        stats.push(stat(todos.filter(function (t) { return !t.done; }).length, "to-dos open"));
        if (habits.length) stats.push(stat(ticks.length + "/" + habits.length, "habits today"));
      }
      container.appendChild(h("div", { class: "dhead" },
        h("div", null,
          h("p", { class: "eyebrow" }, dateLabel()),
          h("h1", null, "Welcome back"),
          h("p", { class: "muted" }, "Pick a section in the sidebar to get going."))));
      if (stats.length) container.appendChild(h("div", { class: "stats" }, stats));
    });
  }

  function renderHome(container) {
    container.appendChild(h("div", { class: "card empty" }, h("p", { class: "muted" }, "Loading your status...")));
    api("/api/status").then(function (status) {
      container.textContent = "";
      if (!status.has_profile) {
        container.appendChild(h("div", { class: "card empty" },
          h("h2", null, "setup"),
          h("h1", null, "Nothing here yet"),
          h("p", { class: "muted" },
            "Open Claude Code in this folder and run /setup. It reads your resume, builds your profile " +
            "and asks a few questions about what you are looking for."),
          h("p", { class: "muted" }, "Your data stays in the me/ folder on this computer.")
        ));
      } else {
        homeSummary(container);
      }
    }).catch(function (err) {
      container.textContent = "";
      container.appendChild(h("div", { class: "card" }, h("p", null, err.message)));
    });
  }

  // ---- tabs ----------------------------------------------------------------

  function showTab(name) {
    Array.prototype.forEach.call(nav.querySelectorAll("button[data-tab]"), function (btn) {
      var on = btn.getAttribute("data-tab") === name;
      btn.classList.toggle("on", on);
      if (on) btn.setAttribute("aria-current", "page");
      else btn.removeAttribute("aria-current");
    });
    saveLastTab(name);
    main.textContent = "";

    if (name === HOME) {
      crumb(HOME);
      return renderHome(main);
    }

    var feature = findFeature(name);
    if (!feature) return showTab(HOME);
    crumb(groupOf(feature) ? groupOf(feature) + " / " + labelOf(feature) : labelOf(feature));

    var tab = feature.tab || {};
    if (tab.style) loadStyle("/features/" + name + "/" + tab.style);

    var ready = tab.script ? loadScript("/features/" + name + "/" + tab.script) : Promise.resolve();
    ready.then(function () {
      var impl = window.NOVI.tabs[name];
      if (!impl || typeof impl.render !== "function") throw new Error("The " + name + " tab did not load.");
      if (name !== currentTab()) return;
      impl.render(main);
    }).catch(function (err) {
      main.textContent = "";
      main.appendChild(h("div", { class: "card" }, h("p", null, err.message)));
    });
  }

  function currentTab() {
    var on = nav.querySelector("button[data-tab].on");
    return on ? on.getAttribute("data-tab") : HOME;
  }

  function navButton(name, label, iconD) {
    return h("button", {
      type: "button",
      "data-tab": name,
      title: label,
      onclick: function () { showTab(name); }
    }, h("span", { class: "ic" }, icon(iconD)), h("span", { class: "tx" }, label));
  }

  // Home first, then top-level features, then one collapsible section per group (in the order features register).
  function buildNav() {
    nav.textContent = "";
    nav.appendChild(navButton(HOME, "home", HOME_ICON));
    features.filter(function (f) { return !groupOf(f); }).forEach(function (f) {
      nav.appendChild(navButton(f.name, labelOf(f), f.icon));
    });
    var groups = [];
    features.forEach(function (f) {
      var g = groupOf(f);
      if (g && groups.indexOf(g) === -1) groups.push(g);
    });
    groups.forEach(function (g) {
      var section = h("details", { class: "grp", "data-grp": g },
        h("summary", null, h("span", { class: "chev", "aria-hidden": "true" }), h("span", { class: "tx" }, g)),
        h("div", { class: "gb" }, features.filter(function (f) { return groupOf(f) === g; }).map(function (f) {
          return navButton(f.name, labelOf(f), f.icon);
        })));
      if (window.NOVI_SHELL) window.NOVI_SHELL.restoreGroup(section);
      nav.appendChild(section);
    });
  }

  function start() {
    api("/api/features").then(function (list) {
      features = list;
      buildNav();
      var wanted = readLastTab();
      var known = [HOME].concat(list.map(function (f) { return f.name; }));
      showTab(known.indexOf(wanted) >= 0 ? wanted : HOME);
    }).catch(function (err) {
      main.appendChild(h("div", { class: "card" }, h("p", null, "Novi could not start: " + err.message)));
    });
  }

  start();
})();
