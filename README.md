# Novi Tracker

A free, private job-search agent that runs on **your own computer** and uses **your own Claude account**. It gives you:

- a **job tracker** board (Pending, Queued, Applied, Interviewing, Offer, Rejected)
- a **Today** tab: to-do list, habits you choose, and streaks
- Claude Code commands that work for *your* search:
  - `/setup` builds your profile and preferences by talking to you
  - `/refresh` searches the web for roles that fit you and adds them to your board
  - `/tailor` writes a resume and cover letter for a role, in the style you choose
  - `/apply` (optional) fills in the application in Chrome and **stops before Submit**
  - `/update` pulls improvements from this repo without touching your data

> **Status:** early version, built for friends. Nothing is hosted. Your resume and job data never leave your computer except through your own Claude session and its web searches.

---

## What you need

| Need | Why | Cost |
|---|---|---|
| A Claude plan (Pro or Max) | Claude Code and Claude in Chrome use your plan. `/refresh` and `/tailor` use some of your usage. | your own plan |
| A computer: Windows 10/11 or Mac | Everything runs locally | free |
| Git | to download and update this repo | free |
| Python 3.11 or newer | runs the tracker app | free |
| Google Chrome | for PDFs and the optional apply step | free |
| Claude Code | the agent | included with your plan |
| Claude in Chrome extension | only for the optional `/apply` step | included with your plan |
| A GitHub account that was invited to this private repo | to download it | free |

---

## Step by step

Do these in order. Copy and paste each command exactly.

### 1. Install Git and Python

**Windows** (open **PowerShell**: press the Windows key, type `PowerShell`, Enter):

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
```

Close PowerShell and open a new one so the commands are found. Check:

```powershell
git --version
py -3 --version
```

**Mac** (open **Terminal**). If you don't have Homebrew, install it from https://brew.sh first, then:

```bash
brew install git python
git --version
python3 --version
```

### 2. Install Claude Code

**Windows (PowerShell):**

```powershell
irm https://claude.ai/install.ps1 | iex
```

**Mac (Terminal):**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Close and reopen the terminal, then check it works:

```
claude --version
```

If the installer commands above don't work, follow the current instructions at https://docs.claude.com/en/docs/claude-code/setup instead (they change sometimes).

### 3. Sign in to Claude Code

```
claude
```

Follow the prompts to sign in with your Claude account. When you see the chat prompt, type `/exit` to leave for now.

### 4. Download this repo

You need to be signed in to GitHub with the account that was invited. The easiest way:

**Windows:**
```powershell
winget install --id GitHub.cli -e
```
**Mac:** `brew install gh`

Then (both):
```
gh auth login
```
Choose GitHub.com, HTTPS, and sign in through the browser. Then:

```
cd ~
git clone https://github.com/shreyamek/novi-tracker.git
cd novi-tracker
```

> If `git clone` says "not found", you haven't accepted the GitHub invitation yet. Check your email or https://github.com/notifications.

### 5. (Optional but recommended) Add Claude in Chrome

Only needed for `/apply`, where Claude fills in application forms for you. You can skip this and add it later.

1. Open Chrome and install **Claude in Chrome** from the Chrome Web Store (search "Claude in Chrome" and pick the one published by Anthropic).
2. Click the extension icon and sign in with the same Claude account.
3. In Claude Code, run `/chrome` to check it's connected. If `/chrome` isn't recognized, restart with `claude --chrome`.
4. When it asks which sites Claude may act on, allow only the job sites you want.

### 6. Start your agent and set up your profile

From inside the `novi-tracker` folder:

```
claude
```

Put your current resume (PDF or Word) into the `me/` folder inside `novi-tracker` (create the folder if it is not there), then type:

```
/setup
```

Claude will read your resume, ask you questions to confirm everything on it, and ask what you want from your search (see **Customizing** below). This takes about 10 minutes. It saves everything to a folder called `me/` that never leaves your computer.

### 7. Open your tracker

Claude will start it for you. If you need to start it yourself later:

- **Windows:** double-click `run.bat`
- **Mac:** `./run.sh`

Then open http://127.0.0.1:8765 in your browser.

### 8. Use it

In Claude Code (in the `novi-tracker` folder) type:

- `refresh`: find new roles that fit you
- `/tailor <company or role>`: write a resume and cover letter for it
- `/apply <company or role>`: fill in the form and stop before Submit (only if you turned it on)

You press Submit yourself every time.

---

## Customizing

Everything about you is in `me/preferences.json`. `/setup` fills it in, and you can edit it any time (or just tell Claude "change my pay floor to $90k").

| Setting | What it does | Options |
|---|---|---|
| `target_roles`, `field`, `level` | What to search for | anything, for example "data analyst", "nurse practitioner", "new grad" |
| `locations`, `remote`, `relocate` | Where you'd work | `remote`, `hybrid`, `onsite`, `any` |
| `pay_floor` | Skip roles that list pay below this | a number or empty |
| `dealbreakers` | Words that rule a role out | for example `clearance required`, `commission only` |
| `fit_threshold` | Minimum fit score (0 to 10) for a role to be added | default `8.0` |
| `search_goals` | What you want from this search, in your own words | free text |
| `tailoring` | How hard to rewrite your resume per job | `light`, `standard`, `aggressive` |
| `apply_mode` | Whether `/apply` is allowed | `off` (default), `prepare` |
| `fill_demographics` | Whether Claude fills voluntary demographic questions | `false` (default) |

**Tailoring levels:** `light` reorders and trims; `standard` rewrites bullets for the role; `aggressive` rewrites freely for keywords and framing. At every level, Claude **never invents facts**. Anything not in your profile (a number, a skill, a tool) is flagged and left out until you confirm it. Your employers, titles, degrees and dates are never changed.

**Habits on the Today tab** are yours to define. Tell Claude: "add habits: gym, read 20 minutes, apply to 1 job".

### Make it your own (fork and branch)

This repo is a base. To build on it:

```
git checkout -b my-version
```

Then ask Claude for what you want ("add a tab for networking contacts"). New features are folders in `app/novi/features/`, see `docs/FEATURES.md`. To get future improvements without losing your changes, run `/update`.

---

## Safety rules (the agent follows these)

- It **never submits** an application, never creates accounts, never types passwords, never solves CAPTCHAs, and never ticks consent or certification boxes.
- It records "Applied" only after you tell it you submitted.
- Roles that need an account (for example many Workday forms) are left in your queue for you to do yourself.
- It does not invent experience. You are responsible for what you submit, so read every document and form before you press Submit.

## Privacy

- Your data is in `me/`, which is excluded from git. Never copy `me/` into the repo or share it.
- `/refresh` uses web search through your own Claude session. There is no telemetry.
- Don't commit your resume or contact details. The check `tools/check_personal_data.py` runs in CI on every push, and you can run it by hand with `py -3 tools/check_personal_data.py` (Mac: `python3 tools/check_personal_data.py`). It is not a pre-commit hook, so run it yourself before you share a change.

## Troubleshooting

| Problem | Fix |
|---|---|
| `claude` not found | Close and reopen the terminal. Re-run the install step. |
| `git clone` fails with "not found" | Accept the GitHub invite, then run `gh auth login` again. |
| The page doesn't open | Make sure the app is running (step 7) and use `http://127.0.0.1:8765`. |
| `/chrome` says not connected | Open Chrome, check the extension is signed in, restart `claude --chrome`. |
| Claude says it's using up your limit | `/refresh` is the heavy one. Run it less often, or lower the number of roles you ask for. |
| Something broke after `/update` | Tell Claude "undo the last update"; your data in `me/` is not touched by updates. |
