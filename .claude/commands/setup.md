---
description: First-time setup. Builds your verified profile from your resume, asks your preferences, and starts the Novi tracker.
---

# /setup

You are setting up Novi Tracker for one person. They may not be a developer. Talk plainly, one or two questions at a time, and keep every answer short. Their data goes only in the git-ignored `me/` folder in this repo. Never write personal data anywhere else, and never put it in a tracked file.

## Rules that always apply

- Never invent or embellish. Every job, project, skill, number and date must come from the resume or from the person's own words.
- Ask before saving any claim the person has not confirmed. Mark each claim `(verified: yes)` or `(verified: no)`.
- Do not apply to jobs, create accounts, or submit anything during setup.
- If something is unclear, ask. Do not guess.

## Step 1: Find the resume

1. Look in the repo folder (the folder that contains `README.md`) for a resume the person dropped in: a `.pdf`, `.docx` or `.txt` file whose name suggests a resume or CV. Ignore `templates/`, `docs/`, `app/` and `tests/`.
2. If there is more than one candidate, list them and ask which one is the resume.
3. If there is none, ask the person to drop their resume into the repo folder and say so. You can still continue by interview, but tell them the profile will be built more slowly.
4. Read the resume. For a PDF, read it directly. For a `.docx`, extract its text (for example with `python -m zipfile` and reading `word/document.xml`, stripping tags). Read the whole resume before asking anything.

## Step 2: Create `me/` and build `me/profile.md`

1. Create the folder `me/` in the repo if it does not exist. Do not change anything outside `me/`.
2. Start from `templates/profile.md`. Copy it to `me/profile.md`.
3. Fill it in section by section, in this order: Summary, Experience, Projects, Skills, Education, Numbers and results.
   - For each job, write the title, employer, location and dates exactly as the resume gives them.
   - For each bullet, keep the wording close to the resume. Each bullet is one claim.
   - Every number, percentage, dollar figure and tool name is a claim. List each one under Numbers and results or with its bullet.
4. Ask the person to confirm each section before moving on. Ask one section at a time, and list the items in it as short numbered lines. Ask: "Is everything here right? Reply with the numbers that are wrong, or 'all good'."
5. Mark each claim `(verified: yes)` once the person confirms it. Mark `(verified: no)` for anything they are unsure of or that you could not find in the resume.
6. Before saving any `verified: no` claim, ask the person whether to keep it. Keep it only as an unverified claim under "Claims not yet confirmed". Never put it in a bullet as if it were confirmed.
7. Ask what is missing that a hiring manager would expect (for example a project, a skill, or a result that is not on the resume). Add it only if the person states it, and mark it as the person's own statement, then ask them to confirm it.

## Step 3: Interview for preferences and write `me/preferences.json`

Start from `templates/preferences.json`. Ask about each key below, one or two questions at a time. Explain the choice in plain words. Write the file only after the person has answered every key or said to skip it.

- **target_roles** (list): the job titles they want. Ask for two to five examples.
- **field** and **level**: the area of work (for example "data analytics") and their level (for example "entry, 0-2 years").
- **locations** (list) and **relocate** (true or false): where they can work, and whether they would move for the right job.
- **remote**: one of `remote`, `hybrid`, `onsite`, `any`. Ask what they prefer and what they can do.
- **pay_floor**: the lowest yearly pay they will accept, as a whole number of dollars, or null if they do not want a floor. Postings without pay are not rejected for this.
- **dealbreakers** (list): words that make a posting an automatic no (for example "commission only", "unpaid"). Ask for examples; leave the list empty if none.
- **start_date**: when they can start, as "YYYY-MM" or "ASAP".
- **work_auth**: their work authorization in their own words (for example "US citizen"). Ask this plainly.
- **sponsorship_needed** (true or false): whether they will need a visa sponsor now or later.
- **tailoring**: explain the three levels, then ask which they want:
  - `light`: reorders and trims the resume. Nothing is reworded.
  - `standard` (default): rewrites bullets so they fit the role, using only the profile's facts.
  - `aggressive`: rewrites freely for keywords and framing, still using only the profile's facts.
  - At every level no facts are invented, employers, titles, degrees and dates never change, and any claim not confirmed in the profile is flagged and left out until the person confirms it.
- **apply_mode**: default `off`. Explain that `prepare` lets Novi fill in a job application in Chrome and stop before Submit. The person always clicks Submit. Offer `prepare` as an option and default to `off` if they are unsure.
- **fill_demographics** (true or false): default false. Explain that if true, Novi may fill in optional demographic questions from answers the person has saved in `me/`. If they are unsure, keep false and leave those questions to them.
- **fit_threshold**: default 8.0 (on a 0 to 10 scale). Explain that roles scoring at or above this are added to the tracker.
- **search_goals**: one or two sentences on what they want from the search in their own words.

Validate the file before you finish. The check is `py -3 -X utf8 -c "import sys; sys.path.insert(0,'app'); import json; from novi import prefs; print(prefs.validate(json.load(open('me/preferences.json', encoding='utf-8'))))"` (use `python3` on Mac). It must print `[]`. Fix any reported problem with the person.

## Step 4: Offer starter habits (optional)

Ask whether they want to track any daily habits in the Today tab. Offer these as examples only: "Apply to one job", "Read 20 minutes", "Walk", "Practice a skill 30 minutes". Ask them to name any they want. Force none. If they want none, skip this step. Save the chosen habits only after they confirm, in `me/habits.json` as a list of `{"key", "label", "hint"}` objects, where `key` is lowercase letters, digits and hyphens.

## Step 5: Check the tools

1. Check that Python 3.11 or newer is installed: `py -3 --version` on Windows or `python3 --version` on Mac. If it is missing, give the install link from python.org and stop until it is installed.
2. Check that git is installed: `git --version`. If it is missing, give the link from git-scm.com and stop until it is installed.
3. Check that Chrome is installed only if the person chose `prepare` mode. Otherwise skip this check.
4. Report each check plainly: found, or what to install.

## Step 6: Start the app

1. On Windows, run `run.bat` in the repo folder. On Mac, run `./run.sh` in the repo folder (make it executable first with `chmod +x run.sh` if needed).
2. Tell the person to open **http://127.0.0.1:8765** in their browser. Explain that this address works only on their own computer.
3. Tell them the next step: say "refresh" in this session to search for roles that fit them. Mention that searching uses their own Claude usage.
4. End with a short summary: what is in `me/`, the tailoring and apply settings they chose, and the fit threshold.

## Stop conditions

- Stop and tell the person if the resume cannot be read.
- Stop if Python or git is missing, and say what to install.
- Never continue to submit, apply or contact anyone.
