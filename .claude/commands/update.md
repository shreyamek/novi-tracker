---
description: Pull upstream Novi Tracker updates into the current branch, resolve conflicts, run tests. Never touches me/.
---

# /update

Brings the upstream template's improvements into the person's current branch. Their own data in `me/` is git-ignored and is never read or changed by this command.

## Hard rules

- **Never open, read, copy or change anything under `me/`.** Git does not track it, so a merge cannot touch it; do not look at it either.
- **Never push.** Local merge only.
- **Never discard the person's changes.** Stop and ask instead of running `reset`, `checkout --` or `stash drop`.
- If upstream changes anything under `me/` (checked in step 5), stop: abort the merge and report.

## Steps

1. **Check the remotes.** Run `git remote -v`.
   - If an `upstream` remote exists, go to step 2.
   - If it does not, look at `origin`. If `origin` is the person's own fork or a URL that is not the Novi Tracker template, ask: "Your origin is `<url>`. Should I add `upstream` pointing at this same URL, or at the template repo `<template url>`?" Wait for the answer. Otherwise run `git remote add upstream <origin-url>`.
   - Never change `origin`.

2. **Fetch.** Run `git fetch upstream`. If it fails (no network, no access, or the template URL is private), stop and report the error.

3. **Clean working tree.** Run `git status --porcelain`. If anything is listed, show it and offer two choices: commit those changes (ask for a message, then `git add <explicit paths>` and commit), or stash them (`git stash push -m "before /update"`). Do not continue until the tree is clean. Do not add files with `git add -A`.

4. **Record the branch.** Run `git branch --show-current`. The merge goes into this branch. If it is detached or empty, stop and ask.

5. **Check for changes under me/.** Run `py -3 -X utf8 tools/update_check.py`.
   - Exit 0: upstream does not touch `me/`. Continue.
   - Exit 1: upstream touches `me/`. Do not merge. Report that the template is changing personal-data paths and tell the person to review it themselves. Stop.
   - Exit 2: the upstream diff could not be read. Stop and report.

6. **Merge.** Run `git merge --no-ff upstream/main`.
   - If there are no conflicts, go to step 7.
   - If there are conflicts, resolve each one by keeping the person's customizations and taking the upstream fix for everything else. Show the person each conflicted file and what you kept, in one line each. If a conflict is about a choice that is theirs (for example their own feature code, a changed default, a renamed route), ask rather than guess.
   - Stage only the resolved files by explicit path, then `git commit --no-edit`.
   - If the merge gets into a state you cannot resolve, run `git merge --abort` and report what happened.

7. **Run the tests.** Run `py -3 -X utf8 -m pytest -q`.
   - If they pass, go to step 8.
   - If they fail, look at the failure. If the merge caused it, fix it in the code and commit the fix (explicit paths). If it cannot be fixed cleanly, run `git merge --abort` (only if the merge is still in progress) or `git reset --hard ORIG_HEAD` after asking the person, then report.

8. **Report.** Give the person a short summary:
   - Branch, upstream commit range (`git log --oneline HEAD~1..HEAD` or the merge range), and files changed.
   - Conflicts: each file and what was kept.
   - Test result: the pytest summary line.
   - Anything not done (for example a stash they still need to pop, or a merge that was aborted).

Commits made by this command end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
