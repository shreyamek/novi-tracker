# Novi Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A private, local-first base repo that gives each friend a tracker board, a Today tab, and Claude Code commands (`/setup`, `/refresh`, `/tailor`, `/apply`, `/update`) running on their own Claude session.

**Architecture:** A Python-stdlib HTTP server bound to 127.0.0.1 serving a static JS/CSS UI, with features as self-registering folders (`app/novi/features/<name>/`). All personal data lives in a git-ignored `me/` folder. The agent behaviour lives in `.claude/commands/*.md`; deterministic checks (claim flagging, personal-data guard) are Python so they can be tested.

**Tech Stack:** Python 3.11+ (stdlib only for the server), vanilla JS/CSS, pytest, Claude Code slash commands, Claude in Chrome (optional).

**Spec:** `docs/superpowers/specs/2026-10-25-novi-tracker-design.md`

**Reuse:** `C:\Users\shrey\Developer\second-brain-ui` (server core, `features/tracker`, `features/today`, static UI). Copy code only. Never copy anything from Shreya's vault, `tracker/data`, cycle, gym, books, Caranect, Tailscale or Firebase code.

## Global Constraints

- Server binds to `127.0.0.1` only; no Tailscale, no remote access, no telemetry.
- Python stdlib only for the server; pytest is the only dev dependency.
- Everything personal is under `me/` and is git-ignored; no real name, email, phone or resume in any tracked file (fixtures use the fake "Alex Example").
- Generated documents never contain a claim missing from `me/profile.md` unless the person confirmed it; employers, titles, degrees and dates are never changed.
- The agent never submits an application, creates an account, types a password, solves a CAPTCHA or ticks a consent/certification box. "Applied" is recorded only after the person says they submitted.
- Tailoring levels are exactly `light`, `standard`, `aggressive`. Apply modes are exactly `off`, `prepare`.
- Status values are exactly `Pending`, `Queued`, `Applied`, `Interviewing`, `Offer`, `Rejected`.
- Commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Review Focus

- Empty `me/` (fresh clone, before `/setup`): the app starts and shows a "run /setup" empty state, no crash.
- Corrupt or hand-edited `me/tracker.json`: the app reports the problem and does not overwrite the file.
- Posting that disappears or is a duplicate of an existing role: `/refresh` skips it and says why.
- Resume containing a number or skill not in the profile: `claims.unsupported_claims` returns it and `/tailor` leaves it out until confirmed.
- Person with no habits defined: Today still renders (to-do list only, streaks hidden).
- Windows paths with spaces and non-ASCII names: storage and scripts work (use `pathlib`, `utf-8`).

---

### Task 1: Skeleton, storage and personal-data guard

**Files:**
- Create: `app/novi/__init__.py`, `app/novi/storage.py`, `app/novi/registry.py`, `tools/check_personal_data.py`, `.gitignore`, `pyproject.toml`
- Test: `tests/test_storage.py`, `tests/test_registry.py`, `tests/test_personal_data_guard.py`

**Interfaces:**
- Produces: `storage.me_dir() -> Path` (env `NOVI_ME` overrides, default `<repo>/me`), `storage.read_json(name: str, default) -> Any`, `storage.write_json(name: str, data) -> None` (atomic write via temp file + rename; refuses to overwrite a file that fails to parse, raising `StorageError`), `registry.register(name: str, routes: dict[str, Callable], tab: dict) -> None`, `registry.features() -> list[dict]`, `tools/check_personal_data.py` exit code 1 if tracked files contain an email address, a phone number, or any path under `me/`.

- [ ] **Step 1: Write failing tests**: `test_read_json_missing_returns_default`, `test_write_json_is_atomic_and_utf8`, `test_write_refuses_to_clobber_corrupt_file` (assert `StorageError` and file bytes unchanged), `test_register_feature_listed_in_order`, `test_guard_flags_email_and_phone_in_tracked_file` (temp git repo fixture), `test_guard_passes_on_fake_alex_example_fixtures`.
- [ ] **Step 2: Run** `py -3 -X utf8 -m pytest -q` → FAIL (modules missing).
- [ ] **Step 3: Implement** the signatures above; `.gitignore` excludes `me/`, `__pycache__/`, `.venv/`, `*.local.*`.
- [ ] **Step 4: Run tests** → PASS.
- [ ] **Step 5: Commit** `feat: skeleton, storage and personal-data guard`.

### Task 2: Server and app shell

**Files:**
- Create: `app/novi/server.py`, `app/novi/static/index.html`, `app/novi/static/app.js`, `app/novi/static/style.css`, `run.bat`, `run.sh`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: `registry.features()`.
- Produces: `server.make_handler(me_dir: Path) -> type[BaseHTTPRequestHandler]`, `server.main(argv: list[str]) -> int` (flags `--port` default 8765, `--me`). `GET /api/features` returns `[{name, tab}]`; unknown `Host` header other than `127.0.0.1:<port>` or `localhost:<port>` gets 403.

- [ ] **Step 1: Write failing tests**: `test_api_features_lists_registered`, `test_non_localhost_host_header_forbidden`, `test_index_served_with_empty_me_dir` (200, body contains "/setup" hint), `test_server_binds_loopback_only`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** with `ThreadingHTTPServer` on `127.0.0.1`; the shell JS builds tabs from `/api/features`; port the layout and CSS tokens from second-brain-ui, with the burgundy accent kept and personal tabs removed.
- [ ] **Step 4: Run** → PASS. **Step 5: Commit** `feat: localhost server and app shell`.

### Task 3: Tracker feature

**Files:**
- Create: `app/novi/features/tracker/{__init__,api,model}.py`, `app/novi/features/tracker/static/tracker.js`, `.css`
- Test: `tests/test_tracker.py`

**Interfaces:**
- Consumes: `storage.read_json/write_json`, `registry.register`.
- Produces: `model.Application` fields `id, company, role, status, link, location, pay, score, score_why, notes, docs, posted, applied, added`; `model.add(app: dict) -> dict` (rejects duplicates on normalized `company+role` or `link`, raising `Duplicate`), `model.set_status(id: str, status: str, date: str | None) -> dict` (rejects values outside the status list), `model.list_all() -> list[dict]`. Routes: `GET /api/tracker`, `POST /api/tracker/add`, `POST /api/tracker/status`, `POST /api/tracker/note`.

- [ ] **Step 1: Write failing tests**: `test_add_rejects_duplicate_link`, `test_add_rejects_duplicate_company_role_case_insensitive`, `test_set_status_rejects_unknown_status`, `test_applied_requires_date_defaults_today`, `test_corrupt_tracker_json_not_overwritten`, `test_empty_me_returns_empty_list`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** (board view grouped by status, search box, detail drawer with notes and docs links; port from second-brain-ui `features/tracker`, drop Shreya-specific sync code). **Step 4: Run** → PASS. **Step 5: Commit** `feat: tracker feature`.

### Task 4: Today feature (to-dos, custom habits, streaks)

**Files:**
- Create: `app/novi/features/today/{__init__,todos,habits,api}.py`, `static/today.js`, `.css`
- Test: `tests/test_todos.py`, `tests/test_habits.py`

**Interfaces:**
- Produces: `todos.add(text) / toggle(id) / move(id, to_index) / set_today(id, flag) / delete(id)` (stored in `me/todos.json`); `habits.define(habits: list[dict])` where a habit is `{key, label, hint}` (stored in `me/habits.json`); `habits.log(date: str, key: str, done: bool)` stored in `me/days/YYYY-MM-DD.json`; `habits.streak(key: str, today: date) -> int` (a streak survives today being not yet ticked); `habits.grid(weeks: int) -> list[dict]`.

- [ ] **Step 1: Write failing tests**: `test_move_reorders`, `test_today_tag_toggle`, `test_streak_counts_consecutive_days_ending_yesterday_when_today_unticked`, `test_streak_breaks_on_gap`, `test_no_habits_defined_returns_empty_grid_and_zero_streaks`, `test_habit_keys_validated_slug_only`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** (port the to-do drag/reorder UI, ring, tiles and contributions grid from second-brain-ui `dashboard.js`; habits are data-driven, no hard-coded wake/read/gym). **Step 4: Run** → PASS. **Step 5: Commit** `feat: today feature`.

### Task 5: Profile, preferences and `/setup`

**Files:**
- Create: `.claude/commands/setup.md`, `templates/profile.md`, `templates/preferences.json`, `tests/fixtures/alex_example/{resume.txt,profile.md,preferences.json}`, `app/novi/prefs.py`
- Test: `tests/test_prefs.py`

**Interfaces:**
- Produces: `prefs.load() -> dict` with keys `target_roles: list[str], field: str, level: str, locations: list[str], remote: "remote"|"hybrid"|"onsite"|"any", relocate: bool, pay_floor: int | None, dealbreakers: list[str], start_date: str, work_auth: str, sponsorship_needed: bool, tailoring: "light"|"standard"|"aggressive", apply_mode: "off"|"prepare", fill_demographics: bool, fit_threshold: float, search_goals: str`; `prefs.validate(d: dict) -> list[str]` returning error strings.

- [ ] **Step 1: Write failing tests**: `test_validate_rejects_bad_tailoring_level`, `test_validate_rejects_bad_apply_mode`, `test_defaults_when_missing` (tailoring `standard`, apply_mode `off`, fill_demographics `false`, fit_threshold `8.0`), `test_fixture_prefs_valid`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** `prefs.py`; write `setup.md` so Claude: reads the dropped resume, builds `me/profile.md` section by section (each job, project, skill, number marked `verified: yes/no` after asking), interviews for each preference key, verifies Python and git are present, creates `me/` and starts the app via `run.bat`/`run.sh`. It must ask before saving every unverified claim and never invent details.
- [ ] **Step 4: Run** → PASS. **Step 5: Commit** `feat: profile, preferences and /setup`.

### Task 6: `/refresh`

**Files:**
- Create: `.claude/commands/refresh.md`, `app/novi/scoring.py`
- Test: `tests/test_scoring.py`

**Interfaces:**
- Consumes: `prefs.load()`, `tracker.model.add`.
- Produces: `scoring.hard_filters(posting: dict, prefs: dict) -> list[str]` (reasons to reject: below pay floor, dealbreaker keyword in title or description, location mismatch for non-relocating onsite, sponsorship needed but not offered); `scoring.dedupe(posting: dict, existing: list[dict]) -> bool`.

- [ ] **Step 1: Write failing tests**: `test_pay_below_floor_rejected_but_unlisted_pay_not`, `test_dealbreaker_keyword_rejected`, `test_onsite_other_city_rejected_when_not_relocating`, `test_dedupe_by_link_and_by_company_role`, `test_closed_posting_flag_respected`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** filters; `refresh.md` tells Claude to use WebSearch/WebFetch with queries built from `prefs`, confirm each posting is still open, apply `hard_filters` and `dedupe`, score fit 0-10 against the person's own goals with a one-line reason, add roles at or above `fit_threshold` as `Pending`, and report added/rejected with reasons. It must not use paid third-party services and must not apply.
- [ ] **Step 4: Run** → PASS. **Step 5: Commit** `feat: /refresh and scoring filters`.

### Task 7: `/tailor` and claim flagging

**Files:**
- Create: `.claude/commands/tailor.md`, `app/novi/claims.py`, `templates/resume.html`, `templates/cover_letter.html`, `tools/render_pdf.py`
- Test: `tests/test_claims.py`

**Interfaces:**
- Produces: `claims.unsupported_claims(doc_text: str, profile_text: str) -> list[str]` returning every number, percentage, dollar figure and known-tool token in the document that does not occur in the profile; `claims.locked_fields_changed(doc_text: str, profile: dict) -> list[str]` returning employers, titles, degrees or dates in the document that differ from the profile.

- [ ] **Step 1: Write failing tests**: `test_new_percentage_flagged`, `test_number_in_profile_not_flagged`, `test_new_tool_flagged`, `test_changed_employer_or_date_flagged`, `test_reordering_and_rewording_not_flagged`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**; `tailor.md` tells Claude to write the documents per tailoring level, run `claims`, leave flagged claims out, show the change list and ask the person to confirm each flagged claim, and render PDFs to `me/docs/` (`tools/render_pdf.py` uses the local Chrome in headless mode, no extra install).
- [ ] **Step 4: Run** → PASS. **Step 5: Commit** `feat: /tailor and claim flagging`.

### Task 8: `/apply` (opt-in)

**Files:**
- Create: `.claude/commands/apply.md`

- [ ] **Step 1:** Port Shreya's `/apply` rules, generalized: gated on `apply_mode == "prepare"`; opens a new Chrome tab (never reuses the person's tabs); fills from `me/profile.md` and `me/preferences.json`; demographic questions only if `fill_demographics` is true and answers exist in `me/`; stops before Submit; lists drafted free-text answers and blanks in the tracker entry notes; never creates accounts, types passwords, solves CAPTCHAs or ticks consent boxes.
- [ ] **Step 2: Verify** by dry-running against the fixture profile on a local static HTML form served by `tests/fixtures/form/` and confirming nothing is submitted. Expected: form filled, Submit untouched.
- [ ] **Step 3: Commit** `feat: /apply (opt-in)`.

### Task 9: `/update`

**Files:**
- Create: `.claude/commands/update.md`, `tools/update_check.py`
- Test: `tests/test_update_check.py`

**Interfaces:**
- Produces: `update_check.touches_me(paths: list[str]) -> bool` (true if any upstream-changed path is under `me/`).

- [ ] **Step 1: Write failing tests**: `test_me_path_detected`, `test_app_path_not_flagged`. **Step 2: Run** → FAIL. **Step 3: Implement**; `update.md` tells Claude to `git fetch upstream`, merge into the person's current branch, resolve conflicts keeping their customizations, run pytest, and abort and report if `touches_me` is true. **Step 4: Run** → PASS. **Step 5: Commit** `feat: /update`.

### Task 10: Docs, CI and repo

**Files:**
- Create: `README.md`, `docs/FEATURES.md`, `.github/workflows/ci.yml`

- [ ] **Step 1:** `README.md` with exact setup steps for Windows and Mac, the Claude and Chrome connection, customization, safety and updates. `FEATURES.md` explains adding a feature folder with a worked example.
- [ ] **Step 2:** CI runs pytest and `tools/check_personal_data.py` on push.
- [ ] **Step 3: Verify** on a clean clone in a temp folder: follow the README literally through `/setup` with the fixture resume. Expected: tracker opens, profile exists, nothing outside `me/` changed.
- [ ] **Step 4: Commit** `docs: README, FEATURES, CI`; create the private GitHub repo, push, invite collaborators when Shreya names them.
