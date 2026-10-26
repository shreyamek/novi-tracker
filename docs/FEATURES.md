# Adding a feature to Novi

Novi is a small local app. The server and the shell are in `app/novi/` (`server.py`, `static/`). Each feature is a folder under `app/novi/features/` that registers its own API routes and its own tab. A feature never edits `core/` code, so you can add one without touching the rest of the app.

The two built-in features are `tracker/` (job board) and `today/` (to-do list, habits, streaks). Use them as reference.

## 1. The folder layout

```
app/novi/features/notes/
  __init__.py        registers the feature (required)
  api.py             the HTTP routes, as plain functions (required if the feature has an API)
  static/
    notes.js         the tab's script (optional, but a tab needs one to draw anything)
    notes.css        the tab's styles (optional)
tests/test_notes.py  tests for the feature
```

Everything under `static/` is served at `/features/notes/<file>`. Nothing outside that folder can be served.

## 2. Register the feature in `__init__.py`

`app/novi/server.py` imports every package in `features/` at startup, so the only thing you must do is call `registry.register` when the package is imported:

```python
"""Notes feature: a short list of free-text notes."""
from novi import registry

from .api import ROUTES

registry.register(
    "notes",
    ROUTES,
    {"label": "Notes", "script": "notes.js", "style": "notes.css"},
)
```

- `name` (first argument): a short unique folder name. Lowercase letters, digits and hyphens.
- `routes`: a dict (shape below).
- `tab`: a dict with the keys below. Only `label` is required.
  - `label`: the text on the tab button.
  - `script`: file name in `static/` that the tab loads. It must set `window.NOVI.tabs[name]`.
  - `style`: file name in `static/` that the tab loads as a stylesheet.

Features appear in the order they are imported (alphabetical by folder name).

## 3. The routes dict

Keys are `"GET /api/<path>"` or `"POST /api/<path>"`. Values are functions that take one argument, `body`, and return a JSON-serialisable value:

```python
from novi import storage

def list_notes(body):                       # GET: body is None
    return {"notes": storage.read_json("notes.json", [])}

def add_note(body):                         # POST: body is the parsed JSON object
    text = str((body or {}).get("text", "")).strip()
    if not text:
        raise ValueError("text is required")          # becomes HTTP 400 with this message
    notes = storage.read_json("notes.json", [])
    notes.append({"text": text[:500]})
    storage.write_json("notes.json", notes)            # atomic; refuses to overwrite a corrupt file
    return {"notes": notes}

ROUTES = {
    "GET /api/notes": list_notes,
    "POST /api/notes/add": add_note,
}
```

Rules the server applies to you:

- Raise `ValueError` for bad input. The server answers 400 with the message.
- `storage.StorageError` (a corrupt data file) answers 500. Let it propagate; do not overwrite the file.
- Any other exception answers 500 and is printed to the terminal. The server keeps running.
- POST bodies must be sent as `application/json` from the same origin. The server rejects other content types (415) and foreign origins (403).

Your data goes in `me/` through `storage.read_json` and `storage.write_json`. Never write personal data anywhere else.

## 4. The tab script and `window.NOVI`

The shell (`static/app.js`) builds the nav from `/api/features`. When the person opens your tab it loads your `script` and then calls `render(container)` on the object you registered under `window.NOVI.tabs[name]`.

`window.NOVI` gives you:

- `h(tag, attrs, ...children)`: builds an element. Children are text or nodes, so server text is never parsed as HTML.
- `api(path, body)`: `GET` when `body` is undefined, otherwise `POST` JSON. Returns a promise. Rejects with an `Error` carrying the server's message.
- `toast(message)`: a short message at the bottom of the page.

Worked `notes` example, `static/notes.js`:

```javascript
"use strict";
(function () {
  var N = window.NOVI;

  function render(container) {
    container.textContent = "";
    var list = N.h("ul", { class: "notes-list" });
    var input = N.h("input", { type: "text", "aria-label": "New note", maxlength: "500" });

    function load() {
      N.api("/api/notes").then(function (data) {
        list.textContent = "";
        data.notes.forEach(function (n) { list.appendChild(N.h("li", null, n.text)); });
      }).catch(function (err) { N.toast(err.message); });
    }

    function add() {
      N.api("/api/notes/add", { text: input.value }).then(function () {
        input.value = "";
        load();
      }).catch(function (err) { N.toast(err.message); });
    }

    container.appendChild(N.h("section", { class: "card" },
      N.h("h2", null, "Notes"),
      list,
      input,
      N.h("button", { type: "button", onclick: add }, "Add")
    ));
    load();
  }

  window.NOVI.tabs.notes = { render: render };
})();
```

Keep the page usable at phone width (16px side gutter, no horizontal scroll). Use the shared styles in `app/novi/static/style.css` where you can.

## 5. Test it

Tests run with pytest from the repo root:

```
py -3 -X utf8 -m pytest -q        (Mac: python3 -m pytest -q)
```

- Use the `me` fixture from `tests/conftest.py`. It points `me/` at a temporary folder, so tests never touch your data.
- Test the route functions directly, for example `api.add_note({"text": "hi"})`, and check bad input raises `ValueError`.
- To test the HTTP behaviour, use the `make_handler` pattern in `tests/test_server.py`.

Example, `tests/test_notes.py`:

```python
import pytest
from novi.features.notes import api

def test_add_note_stores_text(me):
    api.add_note({"text": "call back"})
    assert api.list_notes(None)["notes"] == [{"text": "call back"}]

def test_empty_note_rejected(me):
    with pytest.raises(ValueError):
        api.add_note({"text": "   "})
```

Before you share a change, also run the personal-data check: `py -3 tools/check_personal_data.py` (Mac: `python3 tools/check_personal_data.py`). CI runs it too. It fails if a tracked file has an email address, a phone number, a resume document, or anything under `me/`.

## 6. Checklist

- [ ] `features/<name>/__init__.py` calls `registry.register` with a unique name.
- [ ] Every route key is `GET /api/...` or `POST /api/...` and maps to a function of `body`.
- [ ] Bad input raises `ValueError`. Data is read and written through `storage`.
- [ ] The tab script sets `window.NOVI.tabs[name] = { render: ... }`.
- [ ] Tests pass and `tools/check_personal_data.py` passes.
