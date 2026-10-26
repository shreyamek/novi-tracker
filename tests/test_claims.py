import subprocess
import sys
from pathlib import Path

from novi import claims

PROFILE = """
# Alex Example
Analyst at Acme Corp, 2022-2024. Built Python and SQL reports in Tableau.
Cut report time by 30% and handled 1,200 tickets a week.
Degree: BS Computer Science, 2021.
"""

PROFILE_FIELDS = {
    "employers": ["Acme Corp"],
    "titles": ["Analyst"],
    "degrees": ["BS Computer Science"],
    "dates": ["2022-2024"],
}


def test_new_percentage_flagged():
    doc = "Cut report time by 45% for the sales team."
    assert claims.unsupported_claims(doc, PROFILE) == ["45%"]


def test_number_in_profile_not_flagged():
    doc = "Cut report time by 30% and handled 1,200 tickets a week in 2022."
    assert claims.unsupported_claims(doc, PROFILE) == []


def test_new_tool_flagged():
    doc = "Built dashboards in Python, SQL and Kubernetes."
    assert claims.unsupported_claims(doc, PROFILE) == ["Kubernetes"]


def test_changed_employer_or_date_flagged():
    doc = (
        "EMPLOYER: Acme Corp | TITLE: Analyst | DATES: 2022-2024\n"
        "EMPLOYER: Globex | TITLE: Analyst | DATES: 2022-2024\n"
        "DEGREE: BS Computer Science\n"
        "EMPLOYER: Acme Corp | TITLE: Analyst | DATES: 2019-2024\n"
    )
    flagged = claims.locked_fields_changed(doc, PROFILE_FIELDS)
    assert flagged == [
        "EMPLOYER: Globex | TITLE: Analyst | DATES: 2022-2024",
        "EMPLOYER: Acme Corp | TITLE: Analyst | DATES: 2019-2024",
    ]


def test_reordering_and_rewording_not_flagged():
    # Same facts, reordered fields and reworded bullets: nothing is flagged.
    doc_fields = "DATES: 2022-2024 | TITLE: Analyst | EMPLOYER: Acme Corp\nDEGREE: BS Computer Science\n"
    assert claims.locked_fields_changed(doc_fields, PROFILE_FIELDS) == []
    doc_text = "Reporting analyst at Acme Corp (2022-2024) who ran Python and SQL work in Tableau."
    assert claims.unsupported_claims(doc_text, PROFILE) == []


def test_multipliers_flagged_when_not_in_profile():
    assert claims.unsupported_claims("Reduced latency 3x", PROFILE) == ["3x"]
    assert claims.unsupported_claims("Cut costs 10x overall.", PROFILE) == ["10x"]
    assert claims.unsupported_claims("Made builds 2.5x faster.", PROFILE) == ["2.5x"]


def test_multiplier_in_profile_not_flagged():
    profile = PROFILE + "\nSped up builds 3x and cut costs 10x.\n"
    assert claims.unsupported_claims("Reduced latency 3x", profile) == []
    assert claims.unsupported_claims("Cut costs 10x", profile) == []


def test_go_flagged_as_whole_capitalised_word():
    assert claims.unsupported_claims("Wrote Go services", PROFILE) != []
    assert claims.unsupported_claims("Wrote Go services", PROFILE + "\nBuilt Go services.\n") == []


def test_go_not_triggered_by_google_or_lowercase_go():
    flagged = claims.unsupported_claims("Worked with Google on dashboards.", PROFILE)
    assert "Go" not in flagged
    assert "Go" not in claims.unsupported_claims("We will go to market.", PROFILE)


def test_standalone_capital_r_flagged_and_matched_only_when_present():
    assert claims.unsupported_claims("R and Power Automate", PROFILE) != []
    assert claims.unsupported_claims("R and Power Automate", PROFILE + "\nR and Power Automate.\n") == []


def test_r_inside_words_not_flagged_as_tool():
    flagged = claims.unsupported_claims("Ran reports for regional rollout.", PROFILE)
    assert "R" not in flagged


def test_reworded_sentence_with_only_profile_facts_passes():
    doc = "Reporting analyst at Acme Corp (2022-2024) who ran Python and SQL work in Tableau, cutting time 30%."
    assert claims.unsupported_claims(doc, PROFILE) == []


def test_capitalised_word_absent_from_profile_flagged():
    flagged = claims.unsupported_claims("Led the Globex migration.", PROFILE)
    assert flagged == ["Globex"]


def test_spring_and_express_not_flagged_when_profile_has_them():
    profile = PROFILE + "\nBuilt Spring Boot APIs and Express routes.\n"
    assert claims.unsupported_claims("Built Spring Boot APIs and Express routes.", profile) == []
    assert claims.unsupported_claims("Express routes for the team.", profile) == []


def test_spring_flagged_when_profile_lacks_it():
    assert "Spring" in claims.unsupported_claims("Built Spring Boot APIs.", PROFILE)


def test_own_name_in_document_not_flagged():
    assert claims.unsupported_claims("Alex Example, analyst at Acme Corp.", PROFILE) == []


ALEX_PROFILE = Path(__file__).parent / "fixtures" / "alex_example" / "profile.md"
REPO = Path(__file__).resolve().parents[1]


def test_load_locks_reads_alex_fixture():
    locks = claims.load_locks(ALEX_PROFILE.read_text(encoding="utf-8"))
    assert set(locks) == {"employers", "titles", "degrees", "dates"}
    assert locks["employers"] == ["Example Retail Co.", "Harbor Logistics Example"]
    assert locks["titles"] == ["Data Assistant", "Sales Support Associate"]
    assert locks["dates"] == ["March 2024 to present", "June 2022 to February 2024"]
    assert "Associate of Arts" in locks["degrees"]
    assert "Associate of Arts, Example Community College, 2022" in locks["degrees"]


def test_load_locks_skips_projects_and_unverified_entries():
    text = (
        "# Alex\n"
        "## Experience\n"
        "### Analyst · Acme Corp · 2022 to 2024\n"
        "## Projects\n"
        "### Bike Share Trends · Python, pandas\n"
        "## Education\n"
        "BS Computer Science, State U, 2021 (verified: no)\n"
        "## Claims not yet confirmed\n"
        "- Trip count: about 2 million rows.\n"
    )
    locks = claims.load_locks(text)
    assert locks["employers"] == ["Acme Corp"]
    assert locks["titles"] == ["Analyst"]
    assert locks["dates"] == ["2022 to 2024"]
    assert locks["degrees"] == []


def test_load_locks_empty_profile_gives_empty_lists():
    assert claims.load_locks("") == {"employers": [], "titles": [], "degrees": [], "dates": []}


def test_locked_fields_check_uses_load_locks_on_alex_fixture():
    profile = ALEX_PROFILE.read_text(encoding="utf-8")
    ok = "EMPLOYER: Example Retail Co. | TITLE: Data Assistant | DATES: March 2024 to present\n"
    bad = "EMPLOYER: Globex | TITLE: Data Assistant | DATES: March 2024 to present\n"
    assert claims.locked_fields_changed(ok, claims.load_locks(profile)) == []
    assert claims.locked_fields_changed(bad, claims.load_locks(profile)) == [bad.strip()]


def _run_cli(tmp_path, draft_text):
    draft = tmp_path / "draft.txt"
    draft.write_text(draft_text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(REPO / "app" / "novi" / "claims.py"), str(draft), str(ALEX_PROFILE)],
        capture_output=True, text=True, encoding="utf-8",
    )


def test_cli_passes_clean_draft(tmp_path):
    draft = (
        "EMPLOYER: Example Retail Co. | TITLE: Data Assistant | DATES: March 2024 to present\n"
        "- Wrote SQL queries that cut weekly sales-report prep from 4 hours to 1 hour.\n"
    )
    r = _run_cli(tmp_path, draft)
    assert r.returncode == 0, r.stdout + r.stderr


def test_cli_fails_on_changed_employer_and_prints_it(tmp_path):
    r = _run_cli(tmp_path, "EMPLOYER: Globex | TITLE: Data Assistant | DATES: March 2024 to present\n")
    assert r.returncode == 1
    assert "Globex" in r.stdout


def test_cli_fails_on_unsupported_number_and_prints_it(tmp_path):
    r = _run_cli(tmp_path, "- Cut sales-report prep by 90%.\n")
    assert r.returncode == 1
    assert "UNSUPPORTED" in r.stdout and "90%" in r.stdout
