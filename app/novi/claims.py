"""Flags claims in a generated document that the person's own profile does not support.

Deterministic on purpose: the /tailor command runs this on every draft. Stdlib only.

- unsupported_claims: numbers, percentages, multipliers (3x), dollar figures, known tools, and
  capitalised words in the document that do not appear in the profile text.
- locked_fields_changed: document lines (EMPLOYER / TITLE / DATES / DEGREE fields) whose
  values are not in the profile's employer, title, date and degree lists.

- load_locks: reads the employer, title, degree and date lists from a profile (templates/profile.md format).

CLI: py -3 -X utf8 app/novi/claims.py <draft.txt> <profile.md>
Runs both checks (unsupported_claims and locked_fields_changed with load_locks); prints each problem
as UNSUPPORTED: or LOCKED: and exits 1 if there is any.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KNOWN_TOOLS = [
    # languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Golang", "Go", "R", "Rust", "Ruby", "PHP",
    "Swift", "Kotlin", "Scala", "Perl", "Bash", "PowerShell", "MATLAB", "SAS", "SPSS", "Stata",
    "SQL", "HTML", "CSS", "Dart", "Elixir", "Haskell", "Lua", "Objective-C",
    # frameworks and libraries
    "React", "Angular", "Vue", "Svelte", "Next.js", "Node.js", "Express", "Django", "Flask",
    "FastAPI", "Spring", "Rails", ".NET", "Laravel", "Pandas", "NumPy", "Scikit-learn",
    "TensorFlow", "PyTorch", "Keras", "Spark", "Hadoop", "Kafka", "Airflow", "dbt", "Redux",
    "jQuery", "Bootstrap", "Tailwind", "GraphQL", "Selenium", "Cypress", "Jest", "Pytest", "JUnit",
    # cloud, data and devops
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins",
    "GitHub Actions", "GitLab CI", "CircleCI", "Git", "Linux", "Nginx", "Redis", "MongoDB",
    "PostgreSQL", "MySQL", "Oracle", "SQLite", "DynamoDB", "Snowflake", "BigQuery", "Redshift",
    "Databricks", "Elasticsearch", "Grafana", "Prometheus", "Datadog", "Splunk",
    # analytics, business and design tools
    "Tableau", "Power BI", "Looker", "Excel", "Google Sheets", "Salesforce", "SAP", "Jira",
    "Confluence", "Figma", "Photoshop", "Illustrator", "HubSpot", "Zapier", "Asana", "Trello",
    "Notion", "Stata", "Qualtrics",
]

# Tools matched exactly as written: "Go" and "R" must be capitalised standalone words.
CASE_SENSITIVE_TOOLS = {"Go", "R"}

_NUMBER = re.compile(
    r"(?<![A-Za-z0-9_])\$?\d+(?:,\d{3})*(?:\.\d+)?"
    r"(?:\s?(?:%|percent\b|million\b|billion\b|thousand\b|[kKmMbB](?![A-Za-z])|[xX](?![A-Za-z])))?"
    r"(?![A-Za-z0-9])"
)
_WORD = re.compile(r"(?<![A-Za-z0-9_])[A-Z][A-Za-z0-9+#]*(?:[.\-][A-Za-z0-9+#]+)*(?![A-Za-z0-9_])")
_SUFFIX_CANON = {"percent": "%", "million": "m", "billion": "b", "thousand": "k"}

# Common sentence-opening words and headings. The general check never flags these.
_STOPLIST = frozenset(w.casefold() for w in """
    The I My A An And Or But So If As In On At For With To Of By From Into Over Across Through
    During While When Where Who Which What How This That These Those Our Their His Her Its We You
    They He She It Also All Each Dear Sincerely Thank Hiring Summary Experience Skills Education
    Projects Profile Resume Employer Title Dates Degree Led Built Managed Wrote Reduced Cut Increased
    Designed Developed Created Implemented Launched Owned Delivered Improved Drove Analyzed Automated
    Coordinated Supported Partnered Mentored Achieved Served Maintained Established Produced Presented
    Trained Simplified Streamlined Scaled Migrated Used Helped Spearheaded Architected Optimized
    Tracked Ran Set Made Grew Saved Reported Shipped Worked Hired Answered Handled Took Held
    Interest Growth Passion Excited Eager Thrilled Motivated Ready Committed Excellent Strong
    Team Teams Company Role Opportunity Best Regards Hello Hi Looking Seeking
""".split())

# Common English words that are also tool names or could start a sentence. They are ignored only when
# they open a sentence, so "Built Express apps" still flags Express. Tool names are never stoplisted.
_SENTENCE_START_WORDS = frozenset(w.casefold() for w in """
    Express Focus Grow Help Drive Bring Lead Ensure Contribute Leverage Collaborate Communicate
    Apply Seek Pursue Deliver Love Enjoy Learn Support Keep Make Find Join Take Use Want Work Build
""".split())


def _normalize_number(token: str) -> str:
    t = token.lower().replace("$", "").replace(",", "").replace(" ", "")
    for word, short in _SUFFIX_CANON.items():
        t = t.replace(word, short)
    return t


def _tool_pattern(tool: str) -> re.Pattern[str]:
    flags = 0 if tool in CASE_SENSITIVE_TOOLS else re.IGNORECASE
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(tool) + r"(?![A-Za-z0-9])", flags)


def _in_text(term: str, text: str) -> bool:
    """Whole-word, case-insensitive presence of term in text."""
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])", text, re.IGNORECASE) is not None


def _name_words(profile_text: str) -> set[str]:
    """Words of the profile's first heading (the person's name). They are never flagged."""
    for line in profile_text.splitlines():
        if line.startswith("# "):
            return {w.casefold() for w in _WORD.findall(line)}
    return set()


def _sentence_start(doc_text: str, pos: int) -> bool:
    before = doc_text[:pos].rstrip(" \t\"'(-*•")
    return before == "" or before[-1] in ".!?:;\n"


def unsupported_claims(doc_text: str, profile_text: str) -> list[str]:
    """Return the numbers, tools and capitalised words in doc_text that do not occur in profile_text, in order.

    Capitalised words are checked one at a time, so "Spring Boot" is flagged only when "Spring" or
    "Boot" is missing from the profile. Sentence-opening stop words and sentence-initial -ed/-ing verb
    forms are skipped, and so are the sentence-opening common words in _SENTENCE_START_WORDS (for
    example "Express interest"), which are skipped as tool names too.
    """
    profile_numbers = {_normalize_number(m.group()) for m in _NUMBER.finditer(profile_text)}
    profile_tools = {t.lower() for t in KNOWN_TOOLS if _tool_pattern(t).search(profile_text)}
    name_words = _name_words(profile_text)

    found: list[tuple[int, str, str]] = []  # (position, text as written, dedupe key)
    for m in _NUMBER.finditer(doc_text):
        key = _normalize_number(m.group())
        if key not in profile_numbers:
            found.append((m.start(), m.group(), "num:" + key))
    for tool in KNOWN_TOOLS:
        if tool.lower() in profile_tools:
            continue
        for m in _tool_pattern(tool).finditer(doc_text):
            if tool.casefold() in _SENTENCE_START_WORDS and _sentence_start(doc_text, m.start()):
                continue
            found.append((m.start(), m.group(), "term:" + m.group().casefold()))
    for m in _WORD.finditer(doc_text):
        word = m.group()
        low = word.casefold()
        if low in _STOPLIST or low in name_words:
            continue
        if len(low) > 4 and low.endswith(("ing", "ed")) and _sentence_start(doc_text, m.start()):
            continue
        if low in _SENTENCE_START_WORDS and _sentence_start(doc_text, m.start()):
            continue
        if not _in_text(word, profile_text):
            found.append((m.start(), word, "term:" + low))

    flagged: list[str] = []
    seen: set[str] = set()
    for _, text, key in sorted(found):
        if key not in seen:
            seen.add(key)
            flagged.append(text)
    return flagged


_LOCKED_KEYS = {"EMPLOYER": "employers", "TITLE": "titles", "DEGREE": "degrees", "DATES": "dates"}


def _norm_field(value: str) -> str:
    v = re.sub(r"\s*[-–—]\s*", "-", value.strip())
    return re.sub(r"\s+", " ", v).casefold()


def locked_fields_changed(doc_text: str, profile: dict) -> list[str]:
    """Return each document line whose EMPLOYER/TITLE/DATES/DEGREE value is not in the profile lists.

    Line format: "EMPLOYER: Acme | TITLE: Analyst | DATES: 2022-2024" or "DEGREE: BS Computer Science".
    Field order and wording outside these values are not checked.
    """
    allowed = {
        field: {_norm_field(v) for v in profile.get(list_key, [])}
        for field, list_key in _LOCKED_KEYS.items()
    }
    changed: list[str] = []
    for line in doc_text.splitlines():
        parts = [p for p in line.split("|") if ":" in p]
        for part in parts:
            key, _, value = part.partition(":")
            field = key.strip().upper()
            if field in allowed and _norm_field(value) not in allowed[field]:
                changed.append(line.strip())
                break
    return changed


_HEADING_SEP = "·"  # the middle dot between parts of a profile heading
_VERIFIED_TAG = re.compile(r"\s*\(verified:\s*(yes|no)\)\s*$", re.IGNORECASE)


def _add(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def load_locks(profile_text: str) -> dict:
    """Read the locked fields from a profile written in the templates/profile.md format.

    - Under "## Experience", a heading "### Job title · Employer · Start to end" gives one title,
      one employer and one date range.
    - Under "## Education...", each line gives a degree: the full line, and the part before the first
      comma (so "Associate of Arts, Example College, 2022" yields both forms).
    - Lines or headings marked "(verified: no)" are skipped. Projects and other sections are not locked.
    """
    locks: dict[str, list[str]] = {"employers": [], "titles": [], "degrees": [], "dates": []}
    section = ""
    for raw in profile_text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            section = line[3:].strip().casefold()
            continue
        if line.startswith("### ") and section == "experience":
            if re.search(r"\(verified:\s*no\)", line, re.IGNORECASE):
                continue
            parts = [p.strip() for p in line[4:].split(_HEADING_SEP)]
            if len(parts) == 3 and all(parts):
                title, employer, dates = parts
                _add(locks["titles"], title)
                _add(locks["employers"], employer)
                _add(locks["dates"], dates)
            continue
        if section.startswith("education") and line and not line.startswith(("#", "<!--", "|")):
            if line.startswith("- "):
                line = line[2:].strip()
            if re.search(r"\(verified:\s*no\)", line, re.IGNORECASE):
                continue
            text = _VERIFIED_TAG.sub("", line).strip()
            if text:
                _add(locks["degrees"], text)
                _add(locks["degrees"], text.split(",")[0].strip())
    return locks


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: claims.py <draft.txt> <profile.md>", file=sys.stderr)
        return 2
    doc = Path(argv[0]).read_text(encoding="utf-8")
    profile = Path(argv[1]).read_text(encoding="utf-8")
    problems = [f"UNSUPPORTED: {item}" for item in unsupported_claims(doc, profile)]
    problems += [f"LOCKED: {line}" for line in locked_fields_changed(doc, load_locks(profile))]
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
