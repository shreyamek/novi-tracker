---
description: Draft a tailored resume and cover letter for one role, flag unsupported claims, render PDFs
argument-hint: <company or role from me/tracker.json>
---

# /tailor $ARGUMENTS

You write a resume and cover letter for one role from the person's tracker. Everything comes from their own profile. You never invent facts.

## Hard rules (never break these)

1. **Never invent facts.** Only use what is in `me/profile.md`, or what the person confirms in this session.
2. **Employers, titles, degrees and dates are never changed.** Copy them exactly as written in the profile. You may reorder roles or bullets; you may not rename, merge, split or re-date anything.
3. **Every number, percentage, dollar figure, skill and tool must be in the profile.** Anything else is flagged, not written.
4. **Flagged claims are left out** of the documents until the person confirms each one.
5. Never submit, apply, or create accounts. This command only writes files in `me/docs/` and updates the tracker entry.

## Steps

1. **Find the role.** Read `me/tracker.json` and match `$ARGUMENTS` against company or role (case-insensitive). If there are several matches or none, list the candidates and ask which one. Note the entry's `id`, `company`, `role`, `link`, `pay`, and `notes`.

2. **Read the inputs.**
   - `me/profile.md`: the master profile. This is the only source of facts.
   - `me/preferences.json`: `tailoring` (`light`, `standard` or `aggressive`), `search_goals`, `target_roles`, `field`.
   - The posting at `link` if it is reachable, to pull the keywords the role asks for. If it is not reachable, use the role text in the tracker and say so.

3. **Draft by tailoring level.**
   - `light`: keep the wording of the profile. Reorder roles and bullets so the most relevant come first, and trim what is not relevant. Do not reword.
   - `standard`: everything in `light`, and rewrite bullets so they use the role's language (for example "stakeholder reporting" instead of "weekly emails"), keeping the same facts and numbers.
   - `aggressive`: everything in `standard`, plus free rewording and framing aimed at the role's keywords and the goals in `search_goals`. Facts, numbers and tools still come only from the profile.

4. **Write the drafts** as plain text into a scratch file in the scratchpad (not in the repo), one claim per line, with the locked fields in the same line format used by the checker:
   ```
   EMPLOYER: Acme Corp | TITLE: Analyst | DATES: 2022-2024
   DEGREE: BS Computer Science
   ```
   Then write the full resume text and cover letter text.

5. **Run the checks.**
   ```
   py -3 -X utf8 app/novi/claims.py <draft.txt> me/profile.md
   ```
   This lists every unsupported number and tool (exit 1 if any). For the locked fields, run `claims.locked_fields_changed(doc_text, profile)` from `app/novi/claims.py` (import it with `sys.path` set to `app`), where `profile` is `{"employers": [...], "titles": [...], "degrees": [...], "dates": [...]}` taken from the profile. Any line it returns is a bug in the draft: fix the draft to match the profile, do not flag it.

6. **Handle flagged claims.** Remove every flagged number, tool or skill from the drafts. Then ask the person about each flagged claim, one question per claim: "The profile does not mention X. Did you do this? Yes or no." Use `AskUserQuestion` if available, otherwise ask in plain text.
   - Only if they say yes: add the claim to the drafts, and offer to save it to `me/profile.md` marked `verified: yes` with the date. Do this only if they agree.
   - If no, or no answer: keep it out.

7. **Show the change list** before rendering:
   - Reworded: bullet and summary changes, with before and after.
   - Reordered: what moved.
   - Flagged: each claim left out, and whether the person confirmed it.

8. **Render the PDFs.** Write the final HTML from `templates/resume.html` and `templates/cover_letter.html` (fill the `{{...}}` placeholders; keep the template's CSS). Save the HTML as `me/docs/<company-slug>-resume.html` and `me/docs/<company-slug>-cover-letter.html`, then render:
   ```
   py -3 -X utf8 tools/render_pdf.py me/docs/<company-slug>-resume.html me/docs/<company-slug>-resume.pdf
   py -3 -X utf8 tools/render_pdf.py me/docs/<company-slug>-cover-letter.html me/docs/<company-slug>-cover-letter.pdf
   ```
   Use a lowercase slug with hyphens. If the render fails because no Chrome or Edge is found, tell the person to install one and keep the HTML files.

9. **Record on the tracker entry.** Add the PDF paths (relative to the repo, for example `me/docs/acme-resume.pdf`) to the entry's `docs` list in `me/tracker.json`. Write it through the app's storage (`app/novi/storage.py` `read_json` and `write_json`) so a corrupt file is not overwritten. Add a short note to `notes` saying which tailoring level was used and which claims were left out. Do not change `status`.

10. **Report.** Say which files were written, the change list summary, and any claims still flagged. Remind the person that they are responsible for what they submit.
