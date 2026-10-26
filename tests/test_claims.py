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
