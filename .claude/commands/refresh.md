---
description: Search the web for open roles that fit me/preferences.json, check them, score them, and add the good ones to the tracker as Pending.
---

# /refresh

You search for job postings for the person in this repo and add the good ones to their tracker as **Pending**. You never apply, never submit, never contact anyone, and never draft documents unless the person asks in a separate request.

## Tools and limits

- Use only Claude Code's built-in **WebSearch** and **WebFetch**. Do not use paid job-search services or scrapers.
- Cap a run at **10 new roles**. Stop searching once 10 have been added, and say so in the report.
- Write personal data only inside `me/`. Pass JSON to the Python helpers through stdin, not through files outside `me/`.
- Do not touch anything outside `me/` except reading the repo's own code.

## Step 1: Read the person's data

1. Read `me/preferences.json`. If it is missing, stop and tell the person to run `/setup` first.
2. Read `me/profile.md`. Use it to understand the person's skills and experience. Do not add anything to it.
3. Check the preferences with `py -3 -X utf8 -c "import sys,json; sys.path.insert(0,'app'); from novi import prefs; print(prefs.validate(json.load(open('me/preferences.json', encoding='utf-8'))))"` (use `python3` on Mac). If it prints errors, stop and report them.
4. Read `me/tracker.json` if it exists. It is a JSON list of applications. If it does not exist, treat it as an empty list. If it exists but is not valid JSON, stop and report it. Do not overwrite it.

## Step 2: Build search queries

Build 4 to 8 queries from:
- `target_roles` (each role title, in quotes)
- `field` and `level`
- each entry in `locations`, plus "remote" if `remote` is `remote` or `any`
- words from `search_goals` that describe the work they want

Example pattern: `"Junior Data Analyst" Austin remote SQL`. Vary the wording so the results are not all the same. Run each query with WebSearch.

## Step 3: Pre-filter the results

From the search results, keep only postings that are:
- not already in the tracker (see Step 4), and
- not obviously from a job board that needs an account to view.

Skip anything that is not a single job posting (for example a list page, an article, or a career-advice page).

## Step 4: Dedupe against the tracker

For each candidate, run the dedupe check. Pass the candidate and the tracker list as JSON through stdin. The candidate uses the keys `link`, `company`, `title`. Tracker entries use `link`, `company`, `role`.

```
py -3 -X utf8 -c "import sys,json; sys.path.insert(0,'app'); from novi import scoring; d=json.load(sys.stdin); print(scoring.dedupe(d['posting'], d['existing']))"
```

Feed it `{"posting": {...}, "existing": [...]}` on stdin. If it prints `True`, skip the candidate and record it as "duplicate of an existing entry".

## Step 5: Confirm the posting is still open and read the details

For each remaining candidate, WebFetch the posting. Confirm all of these from the page itself:
- The posting is open. If it says closed, filled, expired, or "no longer accepting applications", it is closed. If the page cannot be loaded, it is not confirmed open. Reject it and say so.
- The location, and whether it is remote, hybrid or onsite.
- The pay range, if the posting shows one. If it shows none, leave pay empty. Do not guess.
- Eligibility: any sponsorship or work-authorization wording.
- The date posted, if shown.

Do not invent any detail. If a field is not on the page, leave it empty.

## Step 6: Run the hard filters

Build a posting dict with these keys: `title`, `company`, `location`, `remote` (`remote`, `hybrid` or `onsite`), `pay_min`, `pay_max` (numbers or null), `description` (the key requirements from the page, plain text), `sponsorship_offered` (true, false or null when unknown), `open` (true or false), `link`.

Run it through the filters, with the posting and preferences on stdin:

```
py -3 -X utf8 -c "import sys,json; sys.path.insert(0,'app'); from novi import scoring; d=json.load(sys.stdin); print(json.dumps(scoring.hard_filters(d['posting'], d['prefs'])))"
```

Feed it `{"posting": {...}, "prefs": <the contents of me/preferences.json>}`. A non-empty list means reject. Record the reasons exactly as printed.

## Step 7: Score the fit

For each posting that passes, score fit from **0 to 10** against the person's own goals in `search_goals`, `target_roles`, `field`, `level`, and the skills in `me/profile.md`. Use these points as a guide:
- 9 or 10: a target role, in their field and level, with skills they can show from the profile, in a location and arrangement they accept.
- 7 or 8: close to a target role, or missing one or two of their stated needs.
- 5 or 6: related, but a clear stretch or a weak match on location, pay or level.
- Below 5: a poor match.

Write one line of reason that names the specific matches or gaps. Use only facts from the posting and the profile. Do not claim the person has a skill that is not in the profile.

## Step 8: Add roles at or above the threshold

Roles with a score at or above `fit_threshold` (default 8.0) are added. Stop after 10 new roles.

Adding always goes through the app's tracker API, which does the duplicate check and assigns the `id`. Never edit `me/tracker.json` by hand and never invent an `id`.

1. Check that the app is running: `GET http://127.0.0.1:8765/api/status` should answer. If it does not, tell the person to start Novi with `run.bat` (Windows) or `./run.sh` (Mac/Linux), wait for them to say it is running, then continue. Do not add roles by editing files.
2. For each role that passes, send `POST http://127.0.0.1:8765/api/tracker/add` with a JSON body using these fields:

| Field | Value |
|---|---|
| `company` | Company name from the posting. |
| `role` | Job title from the posting. |
| `status` | Always `Pending`. |
| `link` | The posting URL. |
| `location` | Location text from the posting, for example `Austin, TX (hybrid)`. |
| `pay` | The posted pay range as text, for example `$70,000 to $85,000`, or empty if not posted. |
| `score` | The fit score (number, 0 to 10). |
| `score_why` | The one-line reason from Step 7. |
| `notes` | A single text string of short factual notes, for example `Found by /refresh on 2026-10-25. Confirmed open.`. The app stores it as the first dated note. |
| `docs` | An empty list `[]`. |
| `posted` | The date posted, `YYYY-MM-DD`, or empty if not shown. |
| `applied` | Empty. Only the person can record an application. |

3. If the response is HTTP 400 with a duplicate message, record the role as "duplicate of an existing entry" and move on. If it is any other 400, record the error text as the reason and move on.
4. The app's response contains the stored role with its `id`. Use it in the report.

## Step 9: Report

End with a plain report:

1. **Added** (count and a line each): company, role, score, location, pay if known, and the reason.
2. **Rejected** (count and a line each): company and role, and the reason. Use the exact filter reasons, or "could not confirm open", or "duplicate of an existing entry", or "fit score X below your threshold of Y".
3. If the run stopped at 10 new roles, say so.
4. A one-line reminder that nothing was applied for, and that the person decides what to apply to.

## Never

- Never edit `me/tracker.json` by hand, and never invent a role `id`. The app assigns it.

- Never apply, fill in a form, create an account, or submit anything.
- Never draft a resume, cover letter or other document unless the person asks in a separate request.
- Never change `me/preferences.json` or `me/profile.md`.
- Never mark a role as applied.
- Never add a role you could not confirm is open.
- Never put personal details (names, emails, phone numbers, addresses) in a posting note, a commit, or a file outside `me/`.
