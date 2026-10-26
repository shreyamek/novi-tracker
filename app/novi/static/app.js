/* Novi app shell: builds the tabs from /api/features and hands each tab a container to render into.
   Helpers on window.NOVI: h (safe element builder), api (JSON fetch), toast (short message).
   Feature tabs register window.NOVI.tabs[name] = { render(container) } from their own script. */
(function () {
  "use strict";

  var LAST_TAB_KEY = "novi.lastTab";
  var HOME = "home";

  // Build an element. Children are text or nodes only; vault or profile text is never parsed as HTML.
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

  var nav = document.getElementById("nav");
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

  // ---- home ----------------------------------------------------------------

  function renderHome(container) {
    container.appendChild(h("div", { class: "card empty" },
      h("h2", null, "home"),
      h("p", { class: "muted" }, "Loading your status...")
    ));
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
        container.appendChild(h("div", { class: "card" },
          h("h2", null, "home"),
          h("h1", null, "Welcome back"),
          h("p", { class: "muted" }, "Pick a section above to get going.")
        ));
      }
    }).catch(function (err) {
      container.textContent = "";
      container.appendChild(h("div", { class: "card" }, h("p", null, err.message)));
    });
  }

  // ---- tabs ----------------------------------------------------------------

  function showTab(name) {
    Array.prototype.forEach.call(nav.children, function (btn) {
      var on = btn.getAttribute("data-tab") === name;
      btn.classList.toggle("on", on);
      btn.setAttribute("aria-current", on ? "page" : "false");
    });
    saveLastTab(name);
    main.textContent = "";

    if (name === HOME) return renderHome(main);

    var feature = features.filter(function (f) { return f.name === name; })[0];
    if (!feature) return showTab(HOME);
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
    var on = nav.querySelector("button.on");
    return on ? on.getAttribute("data-tab") : HOME;
  }

  function buildNav() {
    nav.textContent = "";
    var tabs = [{ name: HOME, label: "Home" }].concat(features.map(function (f) {
      return { name: f.name, label: (f.tab && f.tab.label) || f.name };
    }));
    tabs.forEach(function (t) {
      nav.appendChild(h("button", {
        type: "button",
        "data-tab": t.name,
        onclick: function () { showTab(t.name); }
      }, t.label));
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
