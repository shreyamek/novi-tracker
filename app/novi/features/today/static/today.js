"use strict";
// Today tab, laid out like the Second Brain dashboard: header with eyebrow, greeting and progress ring,
// habit tiles with 14 dots, a two-column grid (to-do list and habit checklist), then the contributions grid.
// Habits come from the server; with none defined only the to-do list shows. All text goes in as text nodes.
(function () {
  const N = window.NOVI;
  const state = { data: null, root: null, dragId: null };

  async function load() {
    state.data = await N.api("/api/today");
  }

  // Runs a write. Every route answers with the full Today payload, so the response replaces the state.
  async function act(path, body) {
    try {
      state.data = await N.api(path, body);
    } catch (e) {
      N.toast(e.message);
    }
    draw();
  }

  const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

  // ------------------------------------------------------------ header and progress ring
  function header(d) {
    const habits = d.habits || [];
    const ticks = d.ticks || [];
    const done = habits.filter((x) => ticks.includes(x.key)).length;
    const todos = d.todos || [];
    const open = todos.filter((t) => !t.done).length;
    const urgent = todos.filter((t) => !t.done && t.today).length;
    const hr = new Date().getHours();
    const greet = hr < 12 ? "Good morning" : hr < 18 ? "Good afternoon" : "Good evening";
    const hello = d.name ? `${greet}, ${d.name}` : greet;
    const dateLabel = new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });

    const parts = [];
    if (habits.length) parts.push(`${done} of ${habits.length} habit${habits.length === 1 ? "" : "s"} done`);
    parts.push(`${plural(open, "to-do")} open${urgent ? `, ${urgent} marked TODAY` : ""}`);

    const kids = [
      N.h("div", {},
        N.h("p", { class: "eyebrow" }, dateLabel),
        N.h("h1", {}, hello),
        N.h("p", { class: "muted" }, parts.join(". ") + ".")),
    ];
    if (habits.length) {
      const pct = Math.round((100 * done) / habits.length);
      kids.push(N.h("div", { class: "ring", style: `--p:${pct}`, role: "img", "aria-label": `${done} of ${habits.length} habits done` },
        N.h("div", { "aria-hidden": "true" }, `${done}/${habits.length}`)));
    }
    return N.h("div", { class: "dhead" }, kids);
  }

  // ------------------------------------------------------------ habit tiles
  function tiles(d) {
    const ticks = d.ticks || [];
    const recent = (d.grid || []).slice(-14);
    return N.h("div", { class: "tiles" }, (d.habits || []).map((hb) => {
      const done = ticks.includes(hb.key);
      const streak = (d.streaks || {})[hb.key] || 0;
      const dots = recent.map((g) => N.h("i", { class: (g.done || []).includes(hb.key) ? "on" : "", title: g.date }));
      return N.h("button", {
        class: "tile" + (done ? " done" : ""),
        type: "button",
        "aria-pressed": String(done),
        onclick: () => act("/api/habits/log", { key: hb.key, done: !done }),
      },
        N.h("span", { class: "tl" }, hb.label),
        N.h("span", { class: "tnum" }, N.h("b", {}, String(streak)), N.h("small", {}, streak === 1 ? " day" : " days")),
        N.h("span", { class: "dots" }, dots),
        N.h("span", { class: "th" }, done ? "Done today" : hb.hint || "Tap to tick today"));
    }));
  }

  // ------------------------------------------------------------ to-do list
  function todoRow(t, i, items) {
    const cls = ["todo"];
    if (t.done) cls.push("done");
    if (t.today) cls.push("urgent");
    const li = N.h("li", { class: cls.join(" "), draggable: "true" });

    li.addEventListener("dragstart", (ev) => {
      state.dragId = t.id;
      ev.dataTransfer.effectAllowed = "move";
      li.classList.add("dragging");
    });
    li.addEventListener("dragend", () => {
      state.dragId = null;
      li.classList.remove("dragging");
    });
    li.addEventListener("dragover", (ev) => {
      if (state.dragId) {
        ev.preventDefault();
        li.classList.add("over");
      }
    });
    li.addEventListener("dragleave", () => li.classList.remove("over"));
    li.addEventListener("drop", (ev) => {
      ev.preventDefault();
      li.classList.remove("over");
      const from = state.dragId;
      state.dragId = null;
      if (from && from !== t.id) act("/api/todo/move", { id: from, to: i });
    });

    const cb = N.h("input", { type: "checkbox", "aria-label": t.text });
    cb.checked = !!t.done;
    cb.addEventListener("change", () => act("/api/todo/toggle", { id: t.id }));

    li.append(
      N.h("span", { class: "grip", "aria-hidden": "true", title: "Drag to reorder" }, "⋮⋮"),
      cb,
      N.h("span", { class: "ct" }, t.text),
      N.h("button", {
        class: "tag" + (t.today ? " on" : ""),
        type: "button",
        "aria-pressed": String(!!t.today),
        title: t.today ? "Remove the TODAY tag" : "Mark as urgent",
        onclick: () => act("/api/todo/today", { id: t.id, today: !t.today }),
      }, "TODAY"),
      N.h("span", { class: "acts" },
        N.h("button", { class: "link", type: "button", disabled: i === 0, "aria-label": "Move up", onclick: () => act("/api/todo/move", { id: t.id, to: i - 1 }) }, "↑"),
        N.h("button", { class: "link", type: "button", disabled: i === items.length - 1, "aria-label": "Move down", onclick: () => act("/api/todo/move", { id: t.id, to: i + 1 }) }, "↓"),
        N.h("button", { class: "link danger", type: "button", onclick: () => act("/api/todo/delete", { id: t.id }) }, "Delete")));
    return li;
  }

  function todoCard(d) {
    const todos = d.todos || [];
    const ul = N.h("ul", { class: "checks todos" });
    if (!todos.length) ul.append(N.h("li", {}, N.h("span", { class: "muted" }, "Nothing yet. Add one below.")));
    todos.forEach((t, i) => ul.append(todoRow(t, i, todos)));

    const input = N.h("input", { type: "text", name: "text", placeholder: "Add a to-do", maxlength: "200", required: true, "aria-label": "To-do" });
    const form = N.h("form", { class: "addrow one" }, input, N.h("button", { class: "primary sm", type: "submit" }, "Add"));
    form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      const text = input.value.trim();
      if (text) act("/api/todo/add", { text });
    });

    const open = todos.filter((t) => !t.done).length;
    return N.h("section", { class: "card" },
      N.h("div", { class: "chead" }, N.h("h2", {}, "To-do"), N.h("span", { class: "muted small" }, `${open} open`)),
      ul,
      form);
  }

  // ------------------------------------------------------------ habit checklist (the same ticks as the tiles)
  function habitsCard(d) {
    const habits = d.habits || [];
    const ticks = d.ticks || [];
    const streaks = d.streaks || {};
    const ul = N.h("ul", { class: "checks habitlist" });
    habits.forEach((hb) => {
      const done = ticks.includes(hb.key);
      const streak = streaks[hb.key] || 0;
      const cb = N.h("input", { type: "checkbox", "aria-label": hb.label });
      cb.checked = done;
      cb.addEventListener("change", () => act("/api/habits/log", { key: hb.key, done: cb.checked }));
      ul.append(N.h("li", { class: done ? "done" : "" },
        cb,
        N.h("span", { class: "ct" }, hb.label),
        N.h("span", { class: "muted small" }, `${streak} ${streak === 1 ? "day" : "days"}`)));
    });
    const open = habits.filter((hb) => !ticks.includes(hb.key)).length;
    return N.h("section", { class: "card" },
      N.h("div", { class: "chead" }, N.h("h2", {}, "Habit tracker"), N.h("span", { class: "muted small" }, `${open} open`)),
      ul);
  }

  // ------------------------------------------------------------ contributions grid
  function level(day, total) {
    if (!day || !total) return 0;
    const n = (day.done || []).length;
    return Math.min(5, Math.ceil((5 * n) / total));
  }

  function contributions(d) {
    const grid = d.grid || [];
    const habits = d.habits || [];
    if (!grid.length || !habits.length) return null;
    const weeks = Math.ceil(grid.length / 7);
    const months = N.h("div", { class: "months", style: `--n:${weeks}` });
    const cols = N.h("div", { class: "weeks", style: `--n:${weeks}` });
    let prevMonth = -1;

    for (let w = 0; w < weeks; w++) {
      const col = N.h("div", { class: "wk" });
      const firstDay = grid[w * 7];
      const first = firstDay ? new Date(firstDay.date + "T00:00:00") : null;
      months.append(N.h("span", {}, first && first.getMonth() !== prevMonth ? first.toLocaleDateString(undefined, { month: "short" }) : ""));
      if (first) prevMonth = first.getMonth();
      for (let r = 0; r < 7; r++) {
        const day = grid[w * 7 + r];
        if (!day) {
          col.append(N.h("i", { class: "c fut" }));
          continue;
        }
        const lv = level(day, habits.length);
        const label = new Date(day.date + "T00:00:00").toLocaleDateString(undefined, { month: "short", day: "numeric" });
        col.append(N.h("i", { class: `c l${lv}`, title: `${label}: ${(day.done || []).length} of ${habits.length} habits` }));
      }
      cols.append(col);
    }
    const dayLab = N.h("div", { class: "dlab" }, ["Mon", "", "Wed", "", "Fri", "", ""].map((x) => N.h("span", {}, x)));
    const legend = N.h("div", { class: "legend" },
      N.h("span", {}, "Less"),
      [0, 1, 2, 3, 4, 5].map((n) => N.h("i", { class: `c l${n}` })),
      N.h("span", {}, "More"));
    return N.h("section", { class: "card" },
      N.h("div", { class: "chead" }, N.h("h2", {}, "Contributions")),
      N.h("div", { class: "calbox", style: `--n:${weeks}` },
        N.h("div", { class: "calhead" }, N.h("span", {}), months),
        N.h("div", { class: "calbody" }, dayLab, cols)),
      legend);
  }

  // ------------------------------------------------------------ screen
  function draw() {
    if (!state.root || !state.data) return;
    const d = state.data;
    const wrap = N.h("div", { class: "dash" }, header(d));
    if ((d.habits || []).length) {
      wrap.append(tiles(d));
      wrap.append(N.h("div", { class: "dgrid" }, todoCard(d), habitsCard(d)));
    } else {
      wrap.append(N.h("p", { class: "hint muted" }, "No habits yet. Add habits by telling Claude, for example \"track gym and reading\"."));
      wrap.append(N.h("div", { class: "dgrid" }, todoCard(d)));
    }
    const grid = contributions(d);
    if (grid) wrap.append(grid);
    state.root.replaceChildren(wrap);
  }

  window.NOVI.tabs["today"] = {
    render(container) {
      state.root = container;
      container.replaceChildren(N.h("p", { class: "muted" }, "Loading..."));
      load()
        .then(() => draw())
        .catch((e) => container.replaceChildren(N.h("div", { class: "card" }, N.h("h2", {}, "Today"), N.h("p", {}, e.message))));
    },
  };
})();
