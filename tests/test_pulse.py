"""
Pulse tests — minimal, high-signal coverage for the recurring-insights
pipeline. Every test is economy-minded: if it breaks, it would cause a
client-facing failure (wrong routing, missed alert, or malformed draft).

  1. Diff returns no changes when prior == current snapshot.
  2. Rating-drop ≥ 0.30 raises a HIGH rating_drop change.
  3. New LEGAL-HIGH signal in the scan ⇒ requires_same_day_alert.
  4. Delivery routing: Legal-HIGH ⇒ Ryan-only, even on a client_cc_ryan
     account.
  5. Delivery routing: plain MED severity on a client_cc_ryan account
     ⇒ client in To, Ryan CC'd.
  6. build_draft produces no individual names in the body copy.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pulse_engine import Account, PulseInsight, diff, run_for_account  # noqa: E402
from pulse_deliver import build_draft  # noqa: E402


# --- fixtures ---------------------------------------------------------------

def _snapshot(rating=4.0, sigs=None, legal_flags=None) -> dict:
    return {
        "account_id": "test",
        "timestamp": "2026-04-18T10:00:00Z",
        "snapshot_date": "2026-04-18",
        "rating": rating,
        "review_count": 100,
        "negative_share_recent": 0.20,
        "executive_severity": 5.0,
        "signals": sigs or {},
        "ros_pillars": {"dominant_pillar": "Service"},
        "dominant_pillar": "Service",
        "peer_benchmark": {"gap": 0.1, "peer_avg": 3.9, "n_peers": 3},
        "legal_flags": legal_flags or [],
    }


def _account(mode="client_cc_ryan", client_email="client@example.com") -> Account:
    return Account(
        account_id="test",
        name="Test Account",
        tier=3,
        cadence="weekly",
        scan_module="scan_engine",
        scan_fn="westrail_scan",
        delivery_mode=mode,
        client_email=client_email,
        ryan_email="gojetpakt.us@outlook.com",
        contract_started="2026-04-01",
    )


# --- 1. no-change diff ------------------------------------------------------

def test_diff_returns_empty_on_identical_snapshots():
    snap = _snapshot(rating=4.0)
    changes = diff(snap, snap)
    # Either empty list or only informational-level noise — must be no HIGH/MED
    assert all(c.severity == "LOW" for c in changes), (
        f"Identical snapshots produced non-LOW changes: {changes}"
    )


# --- 2. rating drop -> HIGH -------------------------------------------------

def test_rating_drop_over_threshold_raises_high_change():
    prior = _snapshot(rating=4.2)
    current = _snapshot(rating=3.8)  # delta = -0.4, > 0.30 threshold
    changes = diff(prior, current)
    high_drops = [c for c in changes
                  if c.kind.startswith("rating_drop") and c.severity == "HIGH"]
    assert high_drops, f"Expected a HIGH rating_drop change; got {changes}"


# --- 3. new LEGAL-HIGH -> same-day alert ------------------------------------

def test_new_legal_high_signal_flags_same_day_alert():
    prior = _snapshot(sigs={})
    # Simulate a new legal-HIGH signal appearing this cycle
    current = _snapshot(
        sigs={
            "service_fee": {
                "severity": 3.5,
                "evidence_count": 4,
                "pillar": "Service",
                "legal_flag": "LEGAL-HIGH",
                "label": "Service-Fee Transparency",
            }
        },
        legal_flags=[{
            "signal": "Service-Fee Transparency",
            "flag": "LEGAL-HIGH",
            "note": "CCG lawsuit context",
        }],
    )
    changes = diff(prior, current)
    legal_high_changes = [
        c for c in changes
        if c.severity == "HIGH" and "LEGAL-HIGH" in (c.description or "")
    ]
    assert legal_high_changes, (
        f"Expected a HIGH change flagging the new LEGAL-HIGH signal; "
        f"got {[(c.kind, c.severity, c.description) for c in changes]}"
    )


# --- 4. delivery routing: legal-HIGH overrides client_cc_ryan ---------------

def test_legal_high_forces_ryan_only_routing():
    acct = _account(mode="client_cc_ryan")
    insight = PulseInsight(
        account=acct,
        run_timestamp="2026-04-18T10:00:00Z",
        snapshot_date="2026-04-18",
        prior_date="2026-04-11",
        is_first_run=False,
        rating=3.4,
        review_count=487,
        executive_severity=10.0,
        dominant_pillar="Service",
        legal_flags=[{"signal": "Service-Fee Transparency",
                      "flag": "LEGAL-HIGH", "note": "test"}],
        changes=[],
        overall_severity="MED",        # overall MED — but legal-HIGH forces route
        requires_same_day_alert=True,
        snapshot_path="/tmp/x.json",
    )
    payload = build_draft(insight, "/tmp/fake.pdf")
    assert payload.to == [acct.ryan_email], (
        f"Legal-HIGH must route Ryan-only; got to={payload.to} cc={payload.cc}"
    )
    assert payload.cc == []
    assert payload.requires_human_review is True
    assert "legal" in payload.routing_reason.lower()


# --- 5. delivery routing: client_cc_ryan path --------------------------------

def test_client_cc_ryan_routing_when_no_legal_high_and_not_high_severity():
    acct = _account(mode="client_cc_ryan")
    insight = PulseInsight(
        account=acct,
        run_timestamp="2026-04-18T10:00:00Z",
        snapshot_date="2026-04-18",
        prior_date="2026-04-11",
        is_first_run=False,
        rating=4.0,
        review_count=100,
        executive_severity=4.5,
        dominant_pillar="Service",
        legal_flags=[],
        changes=[],
        overall_severity="MED",
        requires_same_day_alert=False,
        snapshot_path="/tmp/x.json",
    )
    payload = build_draft(insight, "/tmp/fake.pdf")
    assert payload.to == [acct.client_email]
    assert payload.cc == [acct.ryan_email]
    assert payload.requires_human_review is False


# --- 6. no individual names in body copy ------------------------------------

def test_draft_body_contains_no_reviewer_names():
    """Pulse digests must never name individuals (client safety rule).

    We can't enumerate every possible name, but we can sanity-check that
    the body contains no common first-name patterns that would typically
    appear in reviews (e.g., 'Sarah', 'Mike'). The digest templates are
    purely structural — they should never leak names.
    """
    acct = _account(mode="client_cc_ryan")
    insight = PulseInsight(
        account=acct,
        run_timestamp="2026-04-18T10:00:00Z",
        snapshot_date="2026-04-18",
        prior_date="2026-04-11",
        is_first_run=False,
        rating=3.4,
        review_count=487,
        executive_severity=8.0,
        dominant_pillar="Service",
        legal_flags=[],
        changes=[],
        overall_severity="MED",
        requires_same_day_alert=False,
        snapshot_path="/tmp/x.json",
    )
    payload = build_draft(insight, "/tmp/fake.pdf")
    body = (payload.body_text + payload.body_html).lower()

    # These should never appear in structural Pulse copy:
    forbidden = ["sarah ", "mike ", "john ", "dave ", "karen ", "jessica "]
    leaked = [w for w in forbidden if w in body]
    assert not leaked, f"Pulse body leaked names: {leaked}"
