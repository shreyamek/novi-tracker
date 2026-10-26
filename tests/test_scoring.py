from novi import scoring

PREFS = {
    "pay_floor": 70000,
    "dealbreakers": ["commission only"],
    "locations": ["Austin, TX"],
    "relocate": False,
    "sponsorship_needed": False,
}


def posting(**overrides):
    base = {
        "title": "Junior Data Analyst",
        "company": "Acme",
        "location": "Austin, TX",
        "remote": "hybrid",
        "pay_min": None,
        "pay_max": None,
        "description": "SQL and Python reporting for the operations team.",
        "sponsorship_offered": None,
        "open": True,
        "link": "https://example.com/jobs/1",
    }
    base.update(overrides)
    return base


def test_pay_below_floor_rejected_but_unlisted_pay_not():
    reasons = scoring.hard_filters(posting(pay_max=60000), PREFS)
    assert reasons and any("pay" in r for r in reasons)
    assert scoring.hard_filters(posting(pay_min=None, pay_max=None), PREFS) == []
    assert scoring.hard_filters(posting(pay_max=80000), PREFS) == []


def test_dealbreaker_keyword_rejected():
    assert scoring.hard_filters(posting(description="Commission only, no base pay."), PREFS)
    assert scoring.hard_filters(posting(title="COMMISSION ONLY sales rep"), PREFS)
    assert scoring.hard_filters(posting(), PREFS) == []


def test_onsite_other_city_rejected_when_not_relocating():
    other = posting(remote="onsite", location="Dallas, TX")
    assert scoring.hard_filters(other, PREFS)
    assert scoring.hard_filters(posting(remote="onsite", location="Austin, TX"), PREFS) == []
    assert scoring.hard_filters(other, {**PREFS, "relocate": True}) == []
    # a fully remote role is not a location problem
    assert scoring.hard_filters(posting(remote="remote", location="Dallas, TX"), PREFS) == []


def test_sponsorship_needed_but_not_offered_rejected():
    p = posting(sponsorship_offered=False)
    assert scoring.hard_filters(p, {**PREFS, "sponsorship_needed": True})
    assert scoring.hard_filters(posting(sponsorship_offered=None), {**PREFS, "sponsorship_needed": True}) == []


def test_dedupe_by_link_and_by_company_role():
    existing = [
        {"link": "https://example.com/jobs/9", "company": "Other Co", "role": "Analyst"},
        {"link": "https://example.com/jobs/7", "company": "Acme Corp", "role": "Junior  Data Analyst"},
    ]
    assert scoring.dedupe(posting(link="https://example.com/jobs/9"), existing) is True
    assert scoring.dedupe(posting(company="acme corp", title="junior data analyst", link="https://x.example/new"), existing) is True
    assert scoring.dedupe(posting(company="Brand New Co", title="Analyst", link="https://x.example/new"), existing) is False


def test_closed_posting_flag_respected():
    assert scoring.hard_filters(posting(open=False), PREFS)
    no_flag = posting()
    del no_flag["open"]
    assert scoring.hard_filters(no_flag, PREFS) == []
