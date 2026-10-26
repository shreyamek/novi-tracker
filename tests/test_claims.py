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
