---
description: Prepare one job application in Chrome (fill everything, stop before Submit). Opt-in via apply_mode.
argument-hint: <company or role from me/tracker.json>
---

# /apply $ARGUMENTS

You prepare one application in a new Chrome tab and stop before the final Submit. The person clicks Submit. You never submit.

## Gate

1. Read `me/preferences.json`. If `apply_mode` is not exactly `"prepare"`, stop and say:
   > Apply mode is off. To turn it on, set `"apply_mode": "prepare"` in `me/preferences.json` (or run /setup again and choose Chrome apply). Then run /apply again.
2. Find the role in `me/tracker.json` by company or role (case-insensitive). If several or none match, list them and ask. Use the entry's `link`.
3. If the entry has no tailored documents in `docs`, run `/tailor $ARGUMENTS` first.

## Hard rules (never break these)

- **Never click the final Submit or Apply button**, and never press Enter in a form to submit it.
- **Never create an account, never type a password**, never sign in for the person.
- **Never solve a CAPTCHA.** Stop and tell the person.
- **Never tick consent, certification, terms, or "I confirm" boxes.** Leave them for the person.
- **Never invent answers.** Every answer comes from `me/profile.md` or `me/preferences.json`, or is left blank and flagged.
- **Roles that need an account** (for example Workday or any login-first portal) stay in the queue. Note it in the tracker and move on.
- **Stop and tell the person** on any login wall, unexpected redirect, a page that is not the posting, or a second confirmation page you did not expect.
- Mark the entry `Applied` **only after the person says they submitted.** Never before.

## Steps

1. **Load the browser tools** in one call: ToolSearch with `select:mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__find,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__file_upload,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__tabs_context_mcp`.

2. **Open a NEW tab.** Never reuse or act in the person's existing tabs. Create the tab, then navigate it to the entry's `link`.

3. **Confirm the posting is still open.** Read the page. If it says closed, expired, filled, or shows no apply form, set nothing, tell the person, and stop.

4. **Read the form** (`read_page` / `find`). List every field, its label, and whether it is required.

5. **Fill fields from the person's data:**
   - Name, email, phone, address, links: from `me/profile.md`.
   - Work authorization and sponsorship: `work_auth` and `sponsorship_needed` from `me/preferences.json`.
   - Start date: `start_date`. If the form only offers a choice, pick the closest option on or after it.
   - Pay: the midpoint of the posted range, from the entry's `pay`. Never below `pay_floor`. If the midpoint is below `pay_floor`, enter `pay_floor` only when it is inside the posted range; otherwise leave the field blank and flag it.
   - Relocation: `relocate`. Locations: `locations`, in the order the person listed them.
   - Documents: upload the tailored resume and cover letter PDFs from `me/docs/` for this role with `file_upload`.

6. **Demographic and EEO questions**: fill them only if `fill_demographics` is `true` in `me/preferences.json` **and** the answer is in `me/demographics.json`. Otherwise leave them blank and list them as left for the person.

7. **Free-text answers** ("why do you want to work here", "describe a project", and similar): draft each one only from `me/profile.md` and `me/preferences.json`, keep it short, fill the field, and add the exact text to the entry's `notes` under the heading "Drafted answers (edit before submitting)".

8. **Unknown required questions**: leave blank, do not guess, and list each one in `notes` under "Needs your answer".

9. **Check, do not submit.** Re-read the filled form. Confirm each filled value matches the rules above. Take a screenshot with `computer` if it helps the person review. Leave the page open.

10. **Record in the tracker.** Update the entry's `notes` (keep the existing notes, append the new ones). Write through `app/novi/storage.py` (`read_json` / `write_json`) so a corrupt file is not overwritten. Do not change `status`.

11. **Report** to the person in a short list:
    - Filled: the fields you set.
    - Left blank and why: demographics, unknown required questions, consent and certification boxes, anything flagged.
    - Documents uploaded: file names.
    - Next step: review the tab, tick the consent boxes yourself, and click Submit. Then tell me "I submitted it" and I will mark it Applied.

<!--
Dry run against the fixture (nothing real is touched):
serve tests/fixtures/form/index.html locally (a file:// URL is fine) and run steps 1-9 against it.
Expected: name and email filled, the resume PDF uploads, the consent box stays unticked, and
Submit is never clicked. The fixture's script only writes a message on submit, so an empty
result line means the run was correct.
-->
