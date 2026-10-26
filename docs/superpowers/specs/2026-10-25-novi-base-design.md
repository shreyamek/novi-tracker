# Novi base: design

Name: `novi`. Status: draft for Shreya's review, 2026-10-25.

## Purpose

A free, local-first job-search agent that Shreya's friends clone and run in their **own** Claude Code session. Each person gets a tracker board, a Today tab (to-do list, habits, streaks), and slash commands that search the web for roles that fit them, draft tailored resumes and cover letters, and prepare applications in Chrome. It is a **base**: people fork it, branch it and add features of their own. Nothing is hosted, so it costs nothing to run, and each person's Claude plan pays for their own usage.

Success looks like: a non-developer friend clones the repo, opens it in Claude Code, runs `/setup`, and within about 10 minutes has a working tracker with their own profile; later says `refresh` and gets relevant, scored roles for *their* field with documents they would be comfortable submitting.

## Decisions already made (Shreya, Oct 25, 2026)

- Local-first: one private template repo, run on each person's computer with their own Claude Code (not hosted, not multi-tenant).
- Audience is mixed: some developers, some not. Setup must work for a non-developer by talking to Claude.
- Supports anyone, driven by their own profile (not only new-grad tech).
- Chrome apply step is a per-person preference; the default is fill in and **stop before Submit**.
- Tailoring: per-person level (light, standard, aggressive). Aggressive means free rewording and reordering for the role. **Hard line: no invented facts.** Any claim not in the person's master profile is flagged for them to confirm before it is used. Employers, titles, degrees and dates are never altered. Shreya's own account follows the same rules.
- Distribution: private GitHub repo, friends invited as collaborators. Code only, no personal data. (Repo not created yet; created only after Shreya approves this spec.)
- Scope: the job tracker and a Today tab (to-do list with TODAY tags and reordering, customizable habit tracker, streaks and contributions grid). No cycle, gym, books, watching, Caranect or wiki features. Those can be added later by each person as plug-in features.

## Non-goals

No hosted service, accounts or sync. No auto-submit. No sharing of one person's data with another. No scraping behind logins. Not a replacement for Shreya's personal vault, which stays separate.

## Architecture

```
novi/
  .claude/commands/   /setup /refresh /tailor /apply /update (agent instructions)
  app/                local web app: Python stdlib server + static JS/CSS
    core/             server, storage, auth-free localhost binding, helpers
    features/         one folder per feature: tracker/, today/ (server code, UI file, tests)
    static/           shell, shared styles
  templates/          resume and cover-letter templates, profile skeleton
  docs/               this spec, README, FEATURES.md (how to add a feature)
  me/                 GIT-IGNORED: the person's own data
    profile.md        verified master profile
    preferences.json  field, level, locations, pay floor, dealbreakers, tailoring level, apply mode
    tracker.json      applications
    todos.json, habits.json, days/YYYY-MM-DD.json
    docs/             generated resumes and cover letters (PDF)
```

The app is the existing Second Brain UI's server and tracker, de-personalized and moved to a plug-in layout: `features/<name>/` registers its API routes and its tab, so a fork can add `features/cycle/` without touching `core/`. The server binds to 127.0.0.1 only; there is no Tailscale or remote access in the base.

### Data separation

Everything personal is under `me/`, which `.gitignore` excludes. The repo contains no real names, emails, phone numbers or resumes (only the fake "test friend" fixtures). A pre-commit check and a CI test fail if `me/` content, an email address or a phone number appears in tracked files.

## Commands (agent behaviour)

**/setup.** Reads the resume the person drops in (PDF or docx), builds `profile.md` and interviews them to fill gaps and verify every claim (jobs, projects, skills, numbers). Collects preferences: target roles and field, level, locations and relocation, remote preference, pay floor, dealbreakers, start date, work authorization, tailoring level, whether Chrome apply is on, and whether to answer demographic questions (default: no, left for the person). Creates `me/`, checks Python and Chrome, starts the app.

**/refresh.** Uses Claude Code's built-in web search and fetch (no paid services required). Builds queries from the profile and preferences, finds postings, checks each is still open and matches location, pay and eligibility, scores fit against the person's own criteria, and adds roles at or above their threshold as Pending with a one-line reason. Reports what it added and what it rejected and why. It never applies and never drafts documents unless asked or the person has turned on auto-drafting.

**/tailor `<role>`.** Writes a resume and cover letter PDF to `me/docs/` from `profile.md` according to the tailoring level, aimed at the role and at the person's stated goals for the search. Produces a change list: what was reworded, what was reordered, and every claim not in the profile, flagged for confirmation. Flagged claims are left out until confirmed.

**/apply `<role>`.** Only if apply mode is on. Opens the posting in a new Chrome tab, fills the form from the profile and preferences, stops before Submit. Never creates accounts, enters passwords, solves CAPTCHAs, ticks consent or certification boxes, or submits. Roles that need an account stay in the queue. Free-text answers are drafted from the profile only and listed for the person to edit. "Applied" is recorded only after the person says they submitted.

**/update.** Merges upstream changes into the person's branch, resolves conflicts, runs the tests, and never touches `me/`.

## Tracker and Today

Tracker: board of applications by status (Pending, Queued, Applied, Interviewing, Offer, Rejected), notes, links, documents, fit score and reason, pay, location. Generalizes the current `applications.json` fields. Today: a to-do list, a habit tracker whose habits the person defines (starter examples offered in setup, none forced), streaks and the contributions grid. Habits and days are stored as JSON in `me/`, not in a markdown vault.

## Privacy and safety

- Data stays on the person's computer. The only outbound traffic is the agent's web searches and the person's own Claude session.
- The README states plainly that refresh uses their Claude usage, that the agent prepares but does not submit, and that they are responsible for what they submit.
- No telemetry.
- Honesty rule above applies to every generated document and every drafted form answer.

## Testing

pytest for server, storage and tracker logic (carried over from the existing suite and trimmed). A synthetic "test friend" profile under `tests/fixtures/` with a fake resume is used to dry-run `/setup`, `/refresh` and `/tailor` end to end and to assert that flagged claims never land in a generated document. CI runs the suite and the personal-data check.

## Build order

1. Repo skeleton, plug-in feature layout, de-personalized tracker and Today with `me/` storage.
2. `/setup` and the master profile.
3. `/refresh`.
4. `/tailor` with the change list and flagging.
5. `/apply` (opt-in).
6. `/update`, README, FEATURES.md, private GitHub repo, first-friend trial.

## Open questions (not blocking the spec)

- Resume template look: reuse Shreya's, or offer two or three neutral ones.
- Whether to ship a default fit-scoring rubric or have `/setup` generate one per person (leaning: generated per person from their stated priorities).
