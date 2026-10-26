"""Flags claims in a generated document that the person's own profile does not support.

Deterministic on purpose: the /tailor command runs this on every draft. Stdlib only.

- unsupported_claims: numbers, percentages, dollar figures and known tools in the document
  that do not appear in the profile text.
- locked_fields_changed: document lines (EMPLOYER / TITLE / DATES / DEGREE fields) whose
  values are not in the profile's employer, title, date and degree lists.

CLI: py -3 -X utf8 app/novi/claims.py <draft.txt> <profile.md>   (exit 1 if anything is flagged)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KNOWN_TOOLS = [
    # languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Golang", "Rust", "Ruby", "PHP",
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

_NUMBER = re.compile(
    r"(?<![A-Za-z0-9_])\$?\d+(?:,\d{3})*(?:\.\d+)?"
    r"(?:\s?(?:%|percent\b|million\b|billion\b|thousand\b|[kKmMbB](?![A-Za-z])))?"
    r"(?![A-Za-z0-9])"
)
_SUFFIX_CANON = {"percent": "%", "million": "m", "billion": "b", "thousand": "k"}


def _normalize_number(token: str) -> str:
    t = token.lower().replace("$", "").replace(",", "").replace(" ", "")
    for word, short in _SUFFIX_CANON.items():
        t = t.replace(word, short)
    return t


def _tool_pattern(tool: str) -> re.Pattern[str]:
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(tool) + r"(?![A-Za-z0-9])", re.IGNORECASE)


def unsupported_claims(doc_text: str, profile_text: str) -> list[str]:
    """Return the numbers and known tools in doc_text that do not occur in profile_text, in order."""
    profile_numbers = {_normalize_number(m.group()) for m in _NUMBER.finditer(profile_text)}
    profile_tools = {t.lower() for t in KNOWN_TOOLS if _tool_pattern(t).search(profile_text)}

    found: list[tuple[int, str, str]] = []  # (position, text as written, key)
    for m in _NUMBER.finditer(doc_text):
        key = _normalize_number(m.group())
        if key not in profile_numbers:
            found.append((m.start(), m.group(), "num:" + key))
    for tool in KNOWN_TOOLS:
        if tool.lower() in profile_tools:
            continue
        for m in _tool_pattern(tool).finditer(doc_text):
            found.append((m.start(), m.group(), "tool:" + tool.lower()))

    flagged: list[str] = []
    seen: set[str] = set()
    for _, text, key in sorted(found):
        if key not in seen:
            seen.add(key)
            flagged.append(text)
    return flagged


_LOCKED_KEYS = {"EMPLOYER": "employers", "TITLE": "titles", "DEGREE": "degrees", "DATES": "dates"}


def _norm_field(value: str) -> str:
    v = re.sub(r"\s*[-\u2013\u2014]\s*", "-", value.strip())
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


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: claims.py <draft.txt> <profile.md>", file=sys.stderr)
        return 2
    doc = Path(argv[0]).read_text(encoding="utf-8")
    profile = Path(argv[1]).read_text(encoding="utf-8")
    flagged = unsupported_claims(doc, profile)
    for item in flagged:
        print(f"UNSUPPORTED: {item}")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
