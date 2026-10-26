"use strict";
// Tracker tab: board of roles grouped by status, search, detail panel, add form.
// Every value from the server is inserted as text (h() children), never as HTML.
(function () {
  const N = window.NOVI;
  const state = { roles: [], statuses: [], query: "", openId: null, root: null, adding: false };

  function safeHref(url) {
    try {
      const u = new URL(url);
      return u.protocol === "http:" || u.protocol === "https:" ? u.href : null;
    } catch (e) {
      return null;
    }
  }

  function matches(role, q) {
    if (!q) return true;
    const hay = [role.company, role.role, role.location, role.status, role.score_why]
      .concat((role.notes || []).map((n) => n.text))
      .join(" ")
      .toLowerCase();
    return hay.indexOf(q) !== -1;
  }

  async function load() {
    const d = await N.api("/api/tracker");
    state.roles = d.roles || [];
    state.statuses = d.statuses || [];
  }

  // Runs a write, reloads the roles and redraws. Returns the updated record or null on error.
  async function act(path, body, msg) {
    let result = null;
    try {
      result = await N.api(path, body);
      await load();
      if (msg) N.toast(msg);
    } catch (e) {
      N.toast(e.message);
    }
    draw();
    return result;
  }

  function fact(label, value) {
    return N.h("div", { class: "tr-fact" }, N.h("dt", {}, label), N.h("dd", {}, String(value)));
  }

  // ------------------------------------------------------------ add form
  function addForm() {
    const fields = [
      ["company", "Company", "text", true],
      ["role", "Role", "text", true],
      ["link", "Posting link", "url", false],
      ["location", "Location", "text", false],
      ["pay", "Pay", "text", false],
      ["score", "Fit score (0 to 10)", "number", false],
      ["posted", "Posted", "date", false],
    ];
    const f = N.h("form", { class: "tr-form" });
    fields.forEach(([name, label, type, req]) => {
      const attrs = { name, type, "aria-label": label, placeholder: label };
      if (req) attrs.required = true;
      if (name === "score") {
        attrs.min = "0";
        attrs.max = "10";
        attrs.step = "0.1";
      }
      f.append(N.h("label", { class: "tr-field" }, N.h("span", {}, label), N.h("input", attrs)));
    });
    f.append(
      N.h("label", { class: "tr-field wide" }, N.h("span", {}, "Why it fits"),
        N.h("input", { name: "score_why", type: "text", "aria-label": "Why it fits", placeholder: "One line" })),
      N.h("div", { class: "tr-actions wide" },
        N.h("button", { class: "primary", type: "submit" }, "Add role"),
        N.h("button", { type: "button", onclick: () => { state.adding = false; draw(); } }, "Cancel")));
    f.addEventListener("submit", (ev) => {
      ev.preventDefault();
      const body = {};
      new FormData(f).forEach((v, k) => {
        if (String(v).trim() !== "") body[k] = v;
      });
      act("/api/tracker/add", body, "Role added").then((r) => {
        if (r) state.adding = false;
        draw();
      });
    });
    return f;
  }

  // ------------------------------------------------------------ detail panel
  function detail(role) {
    const href = role.link ? safeHref(role.link) : null;
    const picker = N.h("select", { "aria-label": "Status" },
      state.statuses.map((s) => N.h("option", { value: s, selected: s === role.status }, s)));
    const dateIn = N.h("input", { type: "date", "aria-label": "Applied date", value: role.applied || "" });
    const saveBtn = N.h("button", {
      type: "button",
      onclick: () => {
        const body = { id: role.id, status: picker.value };
        if (picker.value === "Applied" && dateIn.value) body.date = dateIn.value;
        act("/api/tracker/status", body, "Status saved");
      },
    }, "Save status");

    const noteIn = N.h("textarea", { "aria-label": "New note", rows: "2", placeholder: "Add a note" });
    const noteForm = N.h("form", { class: "tr-note" }, noteIn, N.h("button", { type: "submit" }, "Add note"));
    noteForm.addEventListener("submit", (ev) => {
      ev.preventDefault();
      const text = noteIn.value.trim();
      if (text) act("/api/tracker/note", { id: role.id, text }, "Note added");
    });

    const notes = (role.notes || []).slice().reverse().map((n) =>
      N.h("li", {}, N.h("span", { class: "muted small" }, n.date || ""), N.h("p", {}, n.text)));

    return N.h("aside", { class: "tr-detail", "aria-label": "Role details" },
      N.h("div", { class: "tr-detail-head" },
        N.h("div", {},
          N.h("h2", {}, role.company || "Untitled"),
          N.h("p", { class: "muted" }, role.role || "")),
        N.h("button", { type: "button", "aria-label": "Close details", onclick: () => { state.openId = null; draw(); } }, "Close")),
      N.h("dl", { class: "tr-facts" },
        fact("Fit", role.score != null ? `${role.score} / 10` : "not scored"),
        fact("Pay", role.pay || "not listed"),
        fact("Location", role.location || "not listed"),
        fact("Posted", role.posted || "unknown"),
        fact("Applied", role.applied || "not yet"),
        fact("Added", role.added || "")),
      role.score_why ? N.h("p", { class: "tr-why" }, role.score_why) : "",
      href ? N.h("a", { class: "tr-link", href, target: "_blank", rel: "noopener noreferrer" }, "Open posting") : "",
      N.h("div", { class: "tr-status" },
        N.h("label", {}, N.h("span", {}, "Status"), picker),
        N.h("label", {}, N.h("span", {}, "Applied on"), dateIn),
        saveBtn),
      N.h("h3", {}, "Notes"),
      notes.length ? N.h("ul", { class: "tr-notes" }, notes) : N.h("p", { class: "muted small" }, "No notes yet."),
      noteForm);
  }

  // ------------------------------------------------------------ board
  function card(role) {
    const meta = [role.location, role.pay].filter(Boolean).join(" · ");
    const parts = [];
    if (role.score != null) parts.push(N.h("b", { class: "tr-score" }, `${role.score}/10`));
    if (meta) parts.push(N.h("span", {}, meta));
    return N.h("button", {
      class: "tr-card" + (role.id === state.openId ? " open" : ""),
      type: "button",
      onclick: () => { state.openId = role.id; draw(); },
    },
      N.h("span", { class: "tr-co" }, role.company || "Untitled"),
      N.h("span", { class: "tr-role" }, role.role || ""),
      N.h("span", { class: "tr-meta" }, parts));
  }

  function board() {
    const q = state.query.trim().toLowerCase();
    const cols = state.statuses.map((s) => {
      const items = state.roles.filter((r) => r.status === s && matches(r, q));
      return N.h("section", { class: "tr-col", "aria-label": s },
        N.h("header", { class: "tr-col-head" }, N.h("h3", {}, s), N.h("span", { class: "tr-count" }, String(items.length))),
        items.length ? items.map(card) : N.h("p", { class: "muted small" }, "None"));
    });
    return N.h("div", { class: "tr-board" }, cols);
  }

  // Typing in search redraws only the board, so the search box keeps focus.
  function drawBoardOnly() {
    const old = state.root.querySelector(".tr-board");
    if (old) old.replaceWith(board());
    else draw();
  }

  function draw() {
    if (!state.root) return;
    const open = state.roles.find((r) => r.id === state.openId) || null;
    if (state.openId && !open) state.openId = null;

    const search = N.h("input", {
      type: "search", class: "tr-search", placeholder: "Search company, role, notes",
      "aria-label": "Search roles", value: state.query,
    });
    search.addEventListener("input", () => {
      state.query = search.value;
      drawBoardOnly();
    });

    const count = state.roles.length;
    const top = N.h("div", { class: "tr-top" },
      N.h("div", {},
        N.h("h2", {}, "Tracker"),
        N.h("p", { class: "muted small" }, `${count} role${count === 1 ? "" : "s"} tracked`)),
      N.h("button", { class: "primary", type: "button", onclick: () => { state.adding = !state.adding; draw(); } },
        state.adding ? "Close form" : "Add role"));

    const children = [top];
    if (state.adding) children.push(N.h("section", { class: "card tr-addcard" }, N.h("h3", {}, "Add a role"), addForm()));
    if (!count) {
      children.push(N.h("section", { class: "card tr-empty" },
        N.h("h3", {}, "No roles yet"),
        N.h("p", { class: "muted" }, "No roles yet. Say \"refresh\" to Claude to find roles that fit you.")));
    }
    children.push(search);
    children.push(N.h("div", { class: "tr-layout" + (open ? " has-detail" : "") }, board(), open ? detail(open) : ""));
    state.root.replaceChildren(...children);
  }

  // ------------------------------------------------------------ tab contract
  window.NOVI.tabs["tracker"] = {
    render(container) {
      state.root = container;
      container.replaceChildren(N.h("p", { class: "muted" }, "Loading..."));
      load()
        .then(() => draw())
        .catch((e) => container.replaceChildren(
          N.h("div", { class: "card" }, N.h("h2", {}, "Tracker"), N.h("p", {}, e.message))));
    },
  };
})();
