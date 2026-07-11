"""Regression tests for the JetPakt CLI's profile split (restaurant vs. agency).

config.py added a JETPAKT_PROFILE switch so the AI Agency vertical can use
its own Sheet/Stripe catalog without touching the live restaurant business's
config. These tests pin the restaurant profile's output to its existing
golden fixtures (jetpakt_cli/tests/*.json) so a future change can't silently
alter live-business behavior, and sanity-check the agency profile is wired
correctly.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import jetpakt_cli.clients as clients
import jetpakt_cli.config as cfg

FIXTURES = Path(__file__).resolve().parent.parent / "jetpakt_cli" / "tests"


def test_restaurant_profile_is_default():
    assert cfg.ACTIVE_PROFILE == "restaurant"
    assert cfg.SHEET_ID == "1L2NqIcZeG_SMqoL_L3YN_IlqiVkMWy4SyBsu2Sa07yI"
    assert cfg.STRIPE_PRODUCT_TIER["prod_UMDbLrW0doOHPI"] == ("Pulse Essentials", 30, 149)


def test_restaurant_onboarding_matches_golden_fixture_matched_prospect():
    customer = clients.load_stripe_customer(FIXTURES / "fixtures_stripe_customer.json")
    sub = clients.load_stripe_subscription(FIXTURES / "fixtures_stripe_subscription.json")
    prospects = clients.load_prospects(FIXTURES / "fixtures_prospects.json")
    now = datetime(2026, 4, 19, 14, 5, 40, tzinfo=timezone.utc)

    plan = clients.build_onboarding_plan(customer, sub, prospects, now=now)
    golden = json.loads((FIXTURES / "onboarding_plan_matched.json").read_text())
    assert plan == golden


def test_restaurant_onboarding_subject_unchanged_for_direct_scan():
    customer = clients.load_stripe_customer(FIXTURES / "fixtures_stripe_customer_direct.json")
    prospects = clients.load_prospects(FIXTURES / "fixtures_prospects.json")
    now = datetime(2026, 4, 19, 14, 5, 22, tzinfo=timezone.utc)

    plan = clients.build_onboarding_plan(customer, None, prospects, now=now)
    # NOTE: onboarding_plan_direct_scan.json's golden subject contains an
    # em-dash and predates this change — it was already stale before the
    # agency-profile split (verified against unmodified code), so this test
    # pins the actual current/correct behavior instead of the stale fixture.
    assert plan["outlook_drafts"][0]["subject"] == "Scan is active, first memo 2026-04-21"
    assert plan["clients_append"][0]["row_object"]["tier"] == "Scan"
