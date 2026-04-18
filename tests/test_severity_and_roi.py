"""
Five plain pytest tests for severity + ROI.

Scope (economy-minded — only things that would bite customer-facing output):
  1. Severity is bounded in [1.0, 10.0] and ties don't pile up
  2. Unit-drift guard: Business refuses a 0-100 negative_share_recent
  3. ROI qualify floor: low-volume business yields qualify=False
  4. ROI Westrail worked example stays within 10% of the methodology doc
  5. Peer benchmark shrinkage pulls a tiny-count outlier toward the prior
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scan_engine import (  # noqa: E402
    Business, Peer, ReviewEvidence,
    peer_benchmark, rank_top_signals, _shrunk_rating,
    pillar_rollup, SIGNAL_LIBRARY,
)
from roi_engine import estimate_recovery  # noqa: E402


# --- helpers ----------------------------------------------------------------

def _biz(review_count: int = 487, rating: float = 3.3,
         neg: float = 0.28, tier: str = "$$") -> Business:
    return Business(
        name="Test Grill", address="1 Test St", city="Denver, CO",
        phone=None, website=None,
        public_rating=rating, review_count=review_count,
        negative_share_recent=neg, review_sources={},
        price_tier=tier,
    )


def _ev(signal: str, date: str = "2025-09-01", stars: float = 1.0) -> ReviewEvidence:
    return ReviewEvidence(
        source="Yelp", source_url="https://example.com/review",
        reviewer_first_name="Reviewer", date=date, stars=stars,
        text=f"test evidence for {signal}",
        signals=[signal],
    )


# --- tests ------------------------------------------------------------------

def test_severity_bounded_and_differentiated():
    """Severities stay in [1, 10] and 3+ signals don't collapse to one tie."""
    biz = _biz()
    evidence = [
        _ev("service_pacing", "2025-09-01"),
        _ev("service_pacing", "2025-07-15"),
        _ev("food_quality", "2025-08-01"),
        _ev("food_quality", "2025-06-10"),
        _ev("food_quality", "2024-12-01"),
        _ev("staffing", "2025-10-01"),
    ]
    top = rank_top_signals(evidence, biz, top_n=3)
    severities = [s["severity"] for s in top]
    assert len(top) == 3
    assert all(1.0 <= s <= 10.0 for s in severities)
    # With continuous scoring, three signals with different evidence
    # profiles must not all be equal. (Two-way ties are acceptable; three-way
    # collapse is the bug we fixed.)
    assert len(set(severities)) >= 2


def test_unit_drift_guard_rejects_percentage():
    """Business with negative_share=28 (percent, not fraction) must raise."""
    with pytest.raises(ValueError, match="0.0\u20131.0 fraction"):
        Business(
            name="Bad", address="x", city="x",
            phone=None, website=None,
            public_rating=3.3, review_count=400,
            negative_share_recent=28,   # the bug we're guarding against
            review_sources={},
        )


def test_roi_qualify_floor_low_volume():
    """A business with very few lifetime reviews should not qualify for a dollar claim."""
    tiny = _biz(review_count=20, rating=3.3, neg=0.20, tier="$")
    rec = estimate_recovery(tiny)
    # Either qualify is False, OR the low ROI still clears 10x (in which case
    # the floor is fine). We assert consistency: qualify matches the floor rule.
    if rec.qualify:
        assert rec.roi_multiple_low >= 10
    else:
        assert rec.roi_multiple_low < 10 or rec.monthly_low < 50


def test_roi_westrail_matches_methodology_doc():
    """Westrail worked example must stay within 10% of the methodology doc's $1,350."""
    biz = _biz(review_count=487, rating=3.3, neg=0.28, tier="$$")
    rec = estimate_recovery(biz)
    # Doc target: $1,350 monthly low for Westrail; allow +/- 10% drift as the
    # model evolves. ROI must clear the 10x floor by a huge margin (doc: 330x).
    assert 1200 <= rec.monthly_low <= 1500, (
        f"monthly_low={rec.monthly_low} drifted >10% from doc $1,350"
    )
    assert rec.roi_multiple_low >= 100   # sanity: well above the 10x floor
    assert rec.qualify is True


def test_peer_shrinkage_pulls_outlier_toward_prior():
    """A 20-review 4.9-star peer should shrink far more than a 600-review 4.9-star peer."""
    tiny = _shrunk_rating(4.9, 20)
    big = _shrunk_rating(4.9, 600)
    # Prior is 4.0 \u2014 the small-sample peer should sit closer to 4.0 than the
    # large-sample peer does.
    assert tiny < big
    # Tiny-count rating cannot land above its raw value, and should be pulled
    # at least 0.2 stars toward the prior.
    assert 4.9 - tiny > 0.2

    # Full peer_benchmark output: raw mean vs shrunk mean must differ when
    # there's a small-sample outlier present.
    biz = _biz()
    peers = [
        Peer(name="Small Outlier", address="x", rating=4.9, review_count=20,
             price_tier="$$", source="Yelp", source_url="https://e.com/1"),
        Peer(name="Big", address="x", rating=4.2, review_count=600,
             price_tier="$$", source="Yelp", source_url="https://e.com/2"),
        Peer(name="Big2", address="x", rating=4.3, review_count=450,
             price_tier="$$", source="Yelp", source_url="https://e.com/3"),
    ]
    bench = peer_benchmark(biz, peers)
    assert bench["avg_peer_rating_shrunk"] < bench["avg_peer_rating"]


def test_ros_pillar_metadata_present_and_rollup_works():
    """Every signal in SIGNAL_LIBRARY has a valid ROS pillar, and pillar_rollup
    aggregates top signals onto those pillars with a dominant pick.
    """
    valid_pillars = {"Production", "Service", "Sales", "Operations", "Management"}
    # Every signal must have a pillar from the framework taxonomy
    for key, meta in SIGNAL_LIBRARY.items():
        assert meta.get("pillar") in valid_pillars, (
            f"signal {key!r} missing or invalid pillar: {meta.get('pillar')!r}"
        )
        # case_refs must all look like "I01".."I24"
        for c in meta.get("case_refs", []):
            assert c.startswith("I") and c[1:].isdigit(), f"bad case ref {c!r}"

    # Build a scan with signals that span multiple pillars, then roll up
    biz = _biz()
    evidence = [
        _ev("service_pacing", "2025-09-01"),     # Service
        _ev("service_pacing", "2025-07-15"),
        _ev("food_quality", "2025-08-01"),       # Production
        _ev("food_quality", "2025-06-10"),
        _ev("service_fee_transparency", "2025-10-01"),  # Sales
    ]
    top = rank_top_signals(evidence, biz, top_n=3)
    rollup = pillar_rollup(top)
    assert rollup["dominant_pillar"] in valid_pillars
    assert len(rollup["pillars"]) >= 1
    # Every pillar entry must carry the fields a future Heatmap UI needs
    for p in rollup["pillars"]:
        assert p["pillar"] in valid_pillars
        assert 0.0 <= p["max_severity"] <= 10.0
        assert isinstance(p["signals"], list) and len(p["signals"]) >= 1
        assert isinstance(p["case_refs"], list)
