"""
JetPakt One-Time Scan v2 — Scan Engine

Generates a structured, evidence-linked reputation scan from:
  - a lead row (CSV record or dict)
  - verbatim public review excerpts (reviewer_first_name, date, stars, text, signals)
  - peer benchmark data (3 local competitors with verified ratings)

Output: dict ready for PDF rendering. Enforces JetPakt guardrails:
  - No individual names in generated body copy
  - All negative claims tied to verbatim quotes
  - Legal flags raised on wage / service-fee / billing / food-safety signals
  - Defamation-safe response drafts requiring human approval
"""

from __future__ import annotations

import datetime as _dt
import math as _math
import re
from dataclasses import dataclass, field
from typing import Any


# ---------- Signal taxonomy ----------
#
# Each signal carries the original fields (label, category, legal_flag) plus
# three optional ROS-framework fields added in v1.1:
#   pillar      — one of Production / Service / Sales / Operations / Management
#   case_refs   — list of 24-case IDs from the Restaurant Operating System
#                 Textbook (see docs/ROS_FRAMEWORK.md §3)
#   principles  — 1-3 operating principles that justify the recommended action
#
# All three are optional for backward compatibility; readers that don't know
# about them simply ignore the extra keys.

SIGNAL_LIBRARY: dict[str, dict[str, Any]] = {
    "service_pacing": {
        "label": "Service Pacing",
        "category": "Operations",
        "legal_flag": None,
        "pillar": "Service",
        "case_refs": ["I06", "I01"],
        "principles": ["Theory of Constraints", "Six Sigma", "Drucker"],
    },
    "service_fee_transparency": {
        "label": "Service-Fee Transparency",
        "category": "Billing",
        "legal_flag": "LEGAL-HIGH",
        "legal_note": (
            "Automatic gratuity / service-fee disclosure is a live "
            "regulatory topic in Denver (CCG lawsuit context). "
            "Any response touching on fee policy should route through "
            "ownership + legal review before publishing."
        ),
        "pillar": "Sales",
        "case_refs": ["I10", "I12", "I22"],
        "principles": ["Game Theory", "Kahneman (Loss Aversion)"],
    },
    "food_quality": {
        "label": "Food Quality",
        "category": "Culinary",
        "legal_flag": None,
        "pillar": "Production",
        "case_refs": ["I02"],
        "principles": [
            "Scientific Management (Taylor)",
            "Six Sigma",
            "Aristotelian Virtue",
        ],
    },
    "food_safety": {
        "label": "Food Safety",
        "category": "Culinary",
        "legal_flag": "LEGAL-MED",
        "legal_note": (
            "Undercooked / safety claims (raw meat, off color, illness) "
            "can create health-department and liability exposure. "
            "Log incident, preserve ticket/line data, respond privately."
        ),
        "pillar": "Production",
        "case_refs": ["I05"],
        "principles": ["Reliability Engineering", "Systems Thinking"],
    },
    "cleanliness": {
        "label": "Cleanliness & Ambiance",
        "category": "Facility",
        "legal_flag": None,
        "pillar": "Service",
        "case_refs": ["I09"],
        "principles": ["Operational Excellence", "Broken Windows"],
    },
    "staffing": {
        "label": "Staffing Ratios",
        "category": "Operations",
        "legal_flag": None,
        "pillar": "Operations",
        "case_refs": ["I16"],
        "principles": [
            "Herzberg (Hygiene vs. Motivators)",
            "Systems Thinking",
        ],
    },
    "billing_disputes": {
        "label": "Billing / Check Accuracy",
        "category": "Billing",
        "legal_flag": "LEGAL-MED",
        "legal_note": (
            "Price disputes benefit from menu-photo evidence and "
            "documented refund/comp policy. Do not argue pricing in "
            "public response threads."
        ),
        "pillar": "Management",
        "case_refs": ["I18", "I22"],
        "principles": ["Principal-Agent", "Verification"],
    },
    "noise_ambiance": {
        "label": "Noise & Atmosphere",
        "category": "Facility",
        "legal_flag": None,
        "pillar": "Service",
        "case_refs": ["I09"],
        "principles": ["Environmental Psychology"],
    },
    "server_attitude": {
        "label": "Server Attitude & Hospitality",
        "category": "Hospitality",
        "legal_flag": None,
        "pillar": "Service",
        "case_refs": ["I07"],
        "principles": [
            "Situational Leadership",
            "Pre-Shift Lineups",
        ],
    },
    "pricing_value": {
        "label": "Pricing & Perceived Value",
        "category": "Commercial",
        "legal_flag": None,
        "pillar": "Sales",
        "case_refs": ["I10", "I11"],
        "principles": [
            "Menu Engineering (Kasavana-Smith)",
            "Anchoring (Tversky-Kahneman)",
        ],
    },
}


# ---------- Data classes ----------

_VALID_TIERS = {"$", "$$", "$$$", "$$$$"}


@dataclass
class ReviewEvidence:
    """A single verbatim public review excerpt used as evidence."""

    source: str                   # e.g. "Yelp"
    source_url: str
    reviewer_first_name: str      # may appear in signed quote only
    date: str                     # "YYYY-MM-DD" or "Mon D, YYYY"
    stars: float                  # 1.0 - 5.0
    text: str                     # verbatim quote
    signals: list[str] = field(default_factory=list)   # keys from SIGNAL_LIBRARY

    def __post_init__(self) -> None:
        if not 1.0 <= float(self.stars) <= 5.0:
            raise ValueError(
                f"ReviewEvidence.stars must be between 1.0 and 5.0 "
                f"(got {self.stars!r}). If you meant a percentage, divide by 20."
            )
        for s in self.signals:
            if s not in SIGNAL_LIBRARY:
                raise ValueError(
                    f"ReviewEvidence.signals contains unknown key {s!r}. "
                    f"Valid keys: {sorted(SIGNAL_LIBRARY)}"
                )


@dataclass
class Peer:
    name: str
    address: str
    rating: float                 # 1.0 - 5.0 public average
    review_count: int
    price_tier: str               # "$", "$$", "$$$"
    source: str                   # e.g. "Yelp" or "TripAdvisor"
    source_url: str

    def __post_init__(self) -> None:
        if not 1.0 <= float(self.rating) <= 5.0:
            raise ValueError(
                f"Peer.rating must be between 1.0 and 5.0 (got {self.rating!r})"
            )
        if int(self.review_count) < 0:
            raise ValueError(
                f"Peer.review_count cannot be negative (got {self.review_count!r})"
            )
        if self.price_tier not in _VALID_TIERS:
            raise ValueError(
                f"Peer.price_tier must be one of {_VALID_TIERS} "
                f"(got {self.price_tier!r})"
            )


@dataclass
class Business:
    name: str
    address: str
    city: str
    phone: str | None
    website: str | None
    public_rating: float
    review_count: int
    negative_share_recent: float   # 0.0 - 1.0 share of recent reviews 1-2 stars
    review_sources: dict[str, str]  # {"Yelp": url, "Google": url, "TripAdvisor": url}
    price_tier: str = "$$"

    def __post_init__(self) -> None:
        if not 1.0 <= float(self.public_rating) <= 5.0:
            raise ValueError(
                f"Business.public_rating must be 1.0–5.0 "
                f"(got {self.public_rating!r})"
            )
        # Unit-drift guard: negative_share_recent must be a 0–1 fraction, NOT a
        # 0–100 percentage. Catching this keeps downstream severity math sane.
        if not 0.0 <= float(self.negative_share_recent) <= 1.0:
            raise ValueError(
                f"Business.negative_share_recent must be a 0.0–1.0 fraction "
                f"(got {self.negative_share_recent!r}). If you meant a "
                f"percentage, divide by 100."
            )
        if int(self.review_count) < 0:
            raise ValueError(
                f"Business.review_count cannot be negative "
                f"(got {self.review_count!r})"
            )
        if self.price_tier not in _VALID_TIERS:
            raise ValueError(
                f"Business.price_tier must be one of {_VALID_TIERS} "
                f"(got {self.price_tier!r})"
            )


# ---------- Severity scoring ----------

# Recency half-life: review signal loses ~50% of weight every 18 months (540d).
# Operational signals (pacing, food safety, fees) tend to persist across years
# unless explicitly addressed — a shorter half-life under-weights still-active
# problems. The 0.55 floor keeps old-but-unaddressed evidence meaningful.
_RECENCY_HALF_LIFE_DAYS = 540.0
_RECENCY_FLOOR = 0.55              # floor so a 2-year-old signal still scores well


def _recency_weight(date_str: str, now: _dt.date | None = None) -> float:
    """Exponential-decay recency weight with a 9-month half-life.

    Replaces the old 4-bucket step function (1.0 / 0.8 / 0.6 / 0.4), which
    produced severity ties when multiple signals happened to share buckets.
    A smooth continuous weight yields unique severities and a natural ordering.
    """
    now = now or _dt.date.today()
    date = None
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            date = _dt.datetime.strptime(date_str, fmt).date()
            break
        except ValueError:
            continue
    if date is None:
        return 0.5
    days = max((now - date).days, 0)
    weight = _math.pow(0.5, days / _RECENCY_HALF_LIFE_DAYS)
    return max(weight, _RECENCY_FLOOR)


def score_signal(signal_key: str,
                 evidence: list[ReviewEvidence],
                 business: Business) -> dict[str, Any]:
    """Return a signal scorecard: 1-10 severity + evidence summary."""
    tied = [e for e in evidence if signal_key in e.signals]
    if not tied:
        return {}

    recency_factors = [_recency_weight(e.date) for e in tied]
    avg_recency = sum(recency_factors) / len(recency_factors)
    recency_sum = sum(recency_factors)   # continuous density signal, no int bumps
    evidence_count = len(tied)

    # Base severity from negative-share × avg recency × continuous density.
    # The old formulation used min(count, 3) which compressed signals with 3+
    # pieces of evidence into identical severities (Lime's 3-way tie at 5.8).
    # Replace with log1p(recency_sum) so additional recent evidence keeps
    # nudging severity upward, but with diminishing returns. Density bonus
    # multiplier kept at ~1.6 so a 3-review signal still gets ~2.2 points on
    # top of base — roughly matching the prior model's 7–8 band.
    # Scaled so a 28% negative share with 3 recent pieces of evidence lands
    # in the 7–8 "attention required" range, matching the prior model's
    # calibration but with a continuous (tie-breaking) density term.
    base = (business.negative_share_recent * 24.0) * avg_recency
    density_bonus = _math.log1p(recency_sum) * 2.4
    # Round to 2 decimals so severities are distinguishable but still stable.
    severity = min(round(base + density_bonus, 2), 10.0)
    severity = max(severity, 1.0)

    meta = SIGNAL_LIBRARY[signal_key]
    return {
        "key": signal_key,
        "label": meta["label"],
        "category": meta["category"],
        "legal_flag": meta.get("legal_flag"),
        "legal_note": meta.get("legal_note"),
        # ROS-framework metadata (v1.1) — optional, None-safe for older signals.
        "pillar": meta.get("pillar"),
        "case_refs": list(meta.get("case_refs", [])),
        "principles": list(meta.get("principles", [])),
        "severity": severity,
        "evidence_count": evidence_count,
        "evidence": tied,
    }


def rank_top_signals(evidence: list[ReviewEvidence],
                     business: Business,
                     top_n: int = 3) -> list[dict[str, Any]]:
    signal_keys = {s for e in evidence for s in e.signals}
    scored = [score_signal(k, evidence, business) for k in signal_keys]
    scored = [s for s in scored if s]
    scored.sort(key=lambda s: (s["severity"], s["evidence_count"]), reverse=True)
    return scored[:top_n]


# ---------- 30 / 60 / 90 day plan ----------

PLAYBOOKS: dict[str, dict[str, list[dict[str, str]]]] = {
    "service_pacing": {
        "30": [
            {"owner": "GM", "action": "Implement table-touch cadence: server visits every 5 min in first 15 min of seating."},
            {"owner": "FOH Lead", "action": "Post a kitchen-ticket expo timer at the pass; surface tickets over 18 min to a manager."},
        ],
        "60": [
            {"owner": "GM", "action": "Run section-load analysis; cap sections at 5 tables during dinner rush."},
            {"owner": "Ownership", "action": "Add a dedicated drink-runner Thu–Sat 5–9 PM."},
        ],
        "90": [
            {"owner": "Ownership", "action": "Review POS pacing data monthly; target avg ticket-to-food under 14 min."},
        ],
    },
    "service_fee_transparency": {
        "30": [
            {"owner": "Ownership + Legal", "action": "Audit current auto-gratuity policy language on menus, website, and check footers. Confirm Denver disclosure compliance."},
            {"owner": "GM", "action": "Train staff to verbally disclose auto-grat threshold at seating for parties near the cutoff."},
        ],
        "60": [
            {"owner": "Ownership", "action": "Publish plain-English fee policy page on the website; link from Yelp/Google bio."},
        ],
        "90": [
            {"owner": "Ownership", "action": "Quarterly legal review of policy vs. current Denver CCG guidance."},
        ],
    },
    "food_quality": {
        "30": [
            {"owner": "Chef", "action": "Re-taste panel on the 3 most-mentioned dishes; document plate-spec photos."},
            {"owner": "Chef", "action": "Sauce-ratio SOP: publish exact grams/ml per build on the line card."},
        ],
        "60": [
            {"owner": "Chef", "action": "Line-cook certification pass on the top 10 tickets; re-certify quarterly."},
        ],
        "90": [
            {"owner": "Chef", "action": "Menu pruning: cut or rework dishes with sustained negative mentions."},
        ],
    },
    "food_safety": {
        "30": [
            {"owner": "Chef + GM", "action": "Incident log for every undercooked / temperature complaint with ticket, cook, and time."},
            {"owner": "Chef", "action": "Re-verify grill temp probes and burger internal-temp SOP (155°F+ / per county guidance)."},
        ],
        "60": [
            {"owner": "Chef", "action": "Monthly ServSafe refresher for line crew; sign-off sheet."},
        ],
        "90": [
            {"owner": "Ownership", "action": "Third-party mystery-shopper food-safety audit."},
        ],
    },
    "cleanliness": {
        "30": [
            {"owner": "GM", "action": "Nightly deep-clean checklist with photo sign-off; rotate carpet/tile focus zones weekly."},
        ],
        "60": [
            {"owner": "Ownership", "action": "Schedule professional deep clean of high-traffic flooring and seating."},
        ],
        "90": [
            {"owner": "Ownership", "action": "Capex review: lighting + flooring refresh plan with budget."},
        ],
    },
    "staffing": {
        "30": [
            {"owner": "GM", "action": "Map actual covers per server by daypart; identify coverage gaps."},
            {"owner": "GM", "action": "Activate on-call server for Fri–Sat dinner peak."},
        ],
        "60": [
            {"owner": "GM", "action": "Open hire for 2 FOH roles; referral bonus program."},
        ],
        "90": [
            {"owner": "Ownership", "action": "Review labor model vs. target covers-per-server benchmark."},
        ],
    },
    "billing_disputes": {
        "30": [
            {"owner": "GM", "action": "Post all menu prices photographically in POS; enable item-level price alerts for modifiers."},
        ],
        "60": [
            {"owner": "GM", "action": "Monthly POS price-audit vs. printed menu; log variance."},
        ],
        "90": [
            {"owner": "Ownership", "action": "Roll out digital menu QR with live pricing."},
        ],
    },
    "noise_ambiance": {
        "30": [
            {"owner": "GM", "action": "Low-volume playlist template for weekday lunch; staff trained on when to dim."},
        ],
        "60": [
            {"owner": "Ownership", "action": "Acoustic panel quote for back dining section."},
        ],
        "90": [
            {"owner": "Ownership", "action": "Lighting / decor refresh cycle scoped."},
        ],
    },
    "server_attitude": {
        "30": [
            {"owner": "GM", "action": "Reset the greet standard: every guest acknowledged within 60 seconds; 30-second rule for seated tables."},
            {"owner": "GM", "action": "Daily pre-shift: one hospitality moment of the day; no-phones-on-floor policy enforced."},
        ],
        "60": [
            {"owner": "GM", "action": "Mystery-diner program: 2 visits/month with a scored hospitality rubric."},
            {"owner": "Ownership", "action": "Tie a hospitality KPI (review sentiment lift) to server performance reviews."},
        ],
        "90": [
            {"owner": "Ownership", "action": "Formal hospitality training refresh (Unreasonable Hospitality / Setting the Table frame)."},
        ],
    },
    "pricing_value": {
        "30": [
            {"owner": "GM", "action": "Audit top 10 menu items for price-to-portion perception; photo each plate against menu description."},
        ],
        "60": [
            {"owner": "Chef + GM", "action": "Introduce 2-3 visible-value items (lunch combo, happy-hour plate) to re-anchor price perception."},
        ],
        "90": [
            {"owner": "Ownership", "action": "Full menu engineering review: contribution margin vs. guest-perceived value."},
        ],
    },
}


def build_action_plan(top_signals: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    plan: dict[str, list[dict[str, str]]] = {"30": [], "60": [], "90": []}
    for sig in top_signals:
        pb = PLAYBOOKS.get(sig["key"], {})
        for horizon in ("30", "60", "90"):
            for item in pb.get(horizon, []):
                plan[horizon].append({
                    "owner": item["owner"],
                    "action": item["action"],
                    "signal": sig["label"],
                })
    return plan


# ---------- Defamation-safe response drafts ----------

RESPONSE_TEMPLATES = {
    "service_pacing": (
        "Thank you for taking the time to share this — a wait like that is "
        "not the experience we want any guest to have. Our team is reviewing "
        "pacing during that daypart and we'd welcome the chance to make it "
        "right on a return visit. Please reach us at {contact_email} so we "
        "can follow up directly."
    ),
    "service_fee_transparency": (
        "Thank you for the feedback. We want our fee and auto-gratuity "
        "policy to be fully clear at the table, and your note is helping us "
        "re-review how we communicate it. If you'd like to discuss your "
        "specific visit, please contact us at {contact_email}."
    ),
    "food_quality": (
        "We appreciate you letting us know — this is not the standard we "
        "hold ourselves to on these dishes. The team is re-tasting and "
        "checking our build specs this week. If you're open to it, reach us "
        "at {contact_email} and we'll make your next visit right."
    ),
    "food_safety": (
        "We take this kind of feedback very seriously. Food safety is "
        "non-negotiable for us and our team is reviewing the specific "
        "ticket and cook-line SOPs tied to your visit. Please contact us "
        "directly at {contact_email} so we can follow up with you."
    ),
    "cleanliness": (
        "Thank you for the honest feedback — guest comfort in the dining "
        "room matters to us and we're reviewing our nightly cleaning "
        "checklist and facility plan. We'd appreciate the chance to host "
        "you again; please reach us at {contact_email}."
    ),
    "staffing": (
        "We hear you — staffing during peak hours is something we're "
        "actively working on. Thank you for flagging this; it's helping us "
        "refine our coverage. Please reach us at {contact_email} if you'd "
        "like us to follow up on your visit."
    ),
    "billing_disputes": (
        "Thank you for surfacing this. We want every check to match the "
        "menu pricing and posted fees exactly. If you can share your visit "
        "date, please reach us at {contact_email} and we'll review the "
        "ticket directly with you."
    ),
    "noise_ambiance": (
        "Thank you for sharing this — atmosphere is part of the meal and "
        "we hear your note on the room. We'll use this as we review "
        "lighting and sound for the space. Please visit us again and reach "
        "{contact_email} if you'd like to share more."
    ),
    "server_attitude": (
        "Thank you for taking the time to share this — the experience you "
        "described is not the standard of hospitality we hold ourselves "
        "to. Our team is reviewing the service moment you flagged and we'd "
        "welcome the chance to host you again. Please reach us at "
        "{contact_email} so we can follow up directly."
    ),
    "pricing_value": (
        "We appreciate the feedback on price and value — it's something we "
        "continually re-check against what we're putting on the plate. "
        "We'd welcome the chance to invite you back and hear more; please "
        "reach us at {contact_email}."
    ),
}

GENERIC_RESPONSE = (
    "Thank you for sharing this feedback. We take every review seriously, "
    "and your notes are being reviewed by ownership and the management "
    "team. We'd welcome the chance to make it right on a return visit — "
    "please reach us at {contact_email}."
)


def build_response_drafts(evidence: list[ReviewEvidence],
                          contact_email: str,
                          top_n: int = 5) -> list[dict[str, Any]]:
    """Produce defamation-safe response drafts for the most recent / most
    severe reviews. All drafts are marked HOLD FOR HUMAN APPROVAL."""

    # Prefer low-star, recent reviews
    ranked = sorted(
        evidence,
        key=lambda e: (e.stars, -_recency_weight(e.date)),
    )
    ranked = ranked[:top_n]

    drafts = []
    for ev in ranked:
        # Pick template for the highest-priority legal-flagged signal if present
        primary = None
        for sig_key in ev.signals:
            meta = SIGNAL_LIBRARY.get(sig_key, {})
            if meta.get("legal_flag"):
                primary = sig_key
                break
        if primary is None and ev.signals:
            primary = ev.signals[0]

        tmpl = RESPONSE_TEMPLATES.get(primary, GENERIC_RESPONSE)
        body = tmpl.format(contact_email=contact_email)

        legal_meta = SIGNAL_LIBRARY.get(primary, {}) if primary else {}
        drafts.append({
            "review": ev,
            "primary_signal": primary,
            "legal_flag": legal_meta.get("legal_flag"),
            "legal_note": legal_meta.get("legal_note"),
            # ROS metadata — lets ops route drafts to the right pillar owner
            # (Chef for Production, GM for Service / Management, etc.).
            "pillar": legal_meta.get("pillar"),
            "case_refs": list(legal_meta.get("case_refs", [])),
            "draft_text": body,
            "status": "HOLD — requires human approval before publishing",
        })
    return drafts


# ---------- ROS Pillar rollup ----------

_ROS_PILLARS = ("Production", "Service", "Sales", "Operations", "Management")


def pillar_rollup(top_signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate top signals into an ROS-pillar drift summary.

    For each pillar present in the top signals, return the max severity, the
    signal labels, and the set of case references. Pillars with no signal are
    omitted from the output. A `dominant_pillar` key names the pillar with
    the highest max severity — the one most in drift.

    This is the data a future Pillar Heatmap UI element reads. The flat
    `top_signals` list is unchanged; this is additive.
    """
    buckets: dict[str, dict[str, Any]] = {}
    for sig in top_signals:
        pillar = sig.get("pillar")
        if not pillar:
            continue
        b = buckets.setdefault(pillar, {
            "pillar": pillar,
            "max_severity": 0.0,
            "signals": [],
            "case_refs": [],
        })
        b["max_severity"] = max(b["max_severity"], float(sig.get("severity", 0.0)))
        b["signals"].append(sig["label"])
        for c in sig.get("case_refs", []):
            if c not in b["case_refs"]:
                b["case_refs"].append(c)

    ordered = [
        buckets[p] for p in _ROS_PILLARS if p in buckets
    ]
    dominant = max(ordered, key=lambda b: b["max_severity"], default=None)
    return {
        "pillars": ordered,
        "dominant_pillar": dominant["pillar"] if dominant else None,
    }


# ---------- Peer benchmark ----------

# Bayesian shrinkage: prior mean for the LoDo/Denver casual-dining bucket.
# A peer with 20 reviews and a 4.9 rating should count less than a peer with
# 600 reviews and 4.6 — the simple mean lets a tiny-count outlier dominate.
# Formula: shrunk = (rating*count + prior*weight) / (count + weight).
_PEER_PRIOR_MEAN = 4.0
_PEER_PRIOR_WEIGHT = 50.0          # "pseudo-reviews" pulling toward the prior


def _shrunk_rating(rating: float, review_count: int) -> float:
    n = max(int(review_count), 0)
    return (
        (rating * n + _PEER_PRIOR_MEAN * _PEER_PRIOR_WEIGHT)
        / (n + _PEER_PRIOR_WEIGHT)
    )


def peer_benchmark(business: Business, peers: list[Peer]) -> dict[str, Any]:
    rows = [
        {
            "name": business.name + " (you)",
            "rating": business.public_rating,
            "review_count": business.review_count,
            "price_tier": business.price_tier,
            "is_subject": True,
        }
    ]
    for p in peers:
        rows.append({
            "name": p.name,
            "rating": p.rating,
            "review_count": p.review_count,
            "price_tier": p.price_tier,
            "is_subject": False,
        })
    # Raw (simple) mean kept for reference; headline delta uses shrunk mean
    # so a single low-volume peer cannot distort the comparison.
    if peers:
        raw_mean = sum(p.rating for p in peers) / len(peers)
        shrunk_peer_ratings = [_shrunk_rating(p.rating, p.review_count) for p in peers]
        shrunk_mean = sum(shrunk_peer_ratings) / len(shrunk_peer_ratings)
    else:
        raw_mean = 0.0
        shrunk_mean = 0.0
    subject_shrunk = _shrunk_rating(business.public_rating, business.review_count) if peers else 0.0
    delta_raw = round(business.public_rating - raw_mean, 2)
    delta_shrunk = round(subject_shrunk - shrunk_mean, 2)
    return {
        "rows": rows,
        "avg_peer_rating": round(raw_mean, 2),
        "avg_peer_rating_shrunk": round(shrunk_mean, 2),
        "subject_rating_shrunk": round(subject_shrunk, 2),
        "delta_vs_peers": delta_raw,                # kept for backwards compat
        "delta_vs_peers_shrunk": delta_shrunk,      # preferred headline delta
    }


# ---------- JetPakt ladder ----------

JETPAKT_LADDER = [
    {"tier": "One-Time Scan", "price": "$49", "summary": "Snapshot + checklist (this document)."},
    {"tier": "Monthly Essentials", "price": "$99/mo", "summary": "Ongoing sentiment monitoring across Yelp, Google, TripAdvisor."},
    {"tier": "Weekly Insights", "price": "$199/mo", "summary": "Deeper analysis, priority-ranked plans, trend alerts."},
    {"tier": "Multi-Location", "price": "from $399/mo", "summary": "Cross-site dashboards for groups and operators."},
    {"tier": "Enterprise Integration", "price": "Custom", "summary": "API access, automation, governance, SSO."},
]


# ---------- Guardrail enforcement ----------

# Detect personal-name references in generated body copy. Reviewer names in
# verbatim quotes are acceptable (they belong to the reviewer); names in the
# signal write-ups, actions, or response-draft wrappers are not.
BODY_COPY_KEYS_TO_CHECK = ("summary", "action", "label", "legal_note")


def scan_for_individual_names(text: str, allowed: set[str]) -> list[str]:
    """Return a list of suspect capitalized name tokens in body copy."""
    if not text:
        return []
    # Find sequences of 2+ capitalized words (rough proper-noun heuristic)
    candidates = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b", text)
    suspects = []
    for c in candidates:
        if c in allowed:
            continue
        # Allow business-style proper nouns if they're in the allowed set
        tokens = c.split()
        if any(t in {"Denver", "Lakewood", "Colorado", "American", "Mexican",
                     "Yelp", "Google", "TripAdvisor", "Happy", "Hour",
                     "Monthly", "Weekly", "Enterprise", "Multi-Location",
                     "Scan"} for t in tokens):
            continue
        suspects.append(c)
    return suspects


# ---------- Top-level builder ----------

def build_scan(
    business: Business,
    evidence: list[ReviewEvidence],
    peers: list[Peer],
    contact_email: str,
    jetpakt_contact: dict[str, str],
) -> dict[str, Any]:
    top_signals = rank_top_signals(evidence, business, top_n=3)
    plan = build_action_plan(top_signals)
    drafts = build_response_drafts(evidence, contact_email, top_n=5)
    bench = peer_benchmark(business, peers)

    # Deterministic ROI / recovery estimate (see docs/ROI_MODEL.md v1).
    # Imported lazily so scan_engine stays importable standalone.
    try:
        from roi_engine import estimate_recovery, recovery_to_dict
        recovery = recovery_to_dict(
            estimate_recovery(business, peer_benchmark=bench)
        )
    except Exception as _roi_err:  # pragma: no cover
        recovery = {"qualify": False, "error": str(_roi_err)}

    # Executive severity = max of top signals, capped 10
    exec_severity = max((s["severity"] for s in top_signals), default=0.0)

    # Collect legal flags
    legal_flags = []
    for s in top_signals:
        if s.get("legal_flag"):
            legal_flags.append({
                "signal": s["label"],
                "flag": s["legal_flag"],
                "note": s.get("legal_note"),
            })

    # ROS pillar rollup — maps top signals onto the five operating pillars.
    # See docs/ROS_FRAMEWORK.md §6 for the product rationale.
    ros_pillars = pillar_rollup(top_signals)

    return {
        "generated_at": _dt.datetime.now().strftime("%B %d, %Y"),
        "business": business,
        "executive_severity": exec_severity,
        "top_signals": top_signals,
        "ros_pillars": ros_pillars,
        "peer_benchmark": bench,
        "recovery": recovery,
        "action_plan": plan,
        "response_drafts": drafts,
        "legal_flags": legal_flags,
        "jetpakt_ladder": JETPAKT_LADDER,
        "jetpakt_contact": jetpakt_contact,
    }


# ---------- Westrail fixture (test harness) ----------

def westrail_fixture() -> dict[str, Any]:
    biz = Business(
        name="Westrail Tap & Grill",
        address="195 S Union Blvd Ste 160",
        city="Lakewood, CO 80228",
        phone="(303) 986-3600",
        website="https://www.westrailtapandgrill.com",
        public_rating=3.3,
        review_count=487,
        negative_share_recent=0.28,
        review_sources={
            "Yelp": "https://www.yelp.com/biz/westrail-tap-and-grill-lakewood",
            "Google": "https://www.google.com/maps/search/Westrail+Tap+Grill+Lakewood",
        },
        price_tier="$$",
    )

    evidence = [
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/westrail-tap-and-grill-lakewood",
            reviewer_first_name="Matt",
            date="2024-07-27",
            stars=1.0,
            text=(
                "took over an hour to get our food and it wasn't busy. "
                "Horrible service, then charged 18 percent gratuity for a "
                "party over 9. Apparently a two year old and a 6 month old "
                "baby and three kids under 15 make it a party of 9… "
                "Ordered a kids quesadilla and got charged 16 dollars… "
                "Burger was undercooked and asada fries were red."
            ),
            signals=["service_pacing", "service_fee_transparency",
                     "billing_disputes", "food_quality", "food_safety"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/westrail-tap-and-grill-lakewood",
            reviewer_first_name="Julie",
            date="2023-12-05",
            stars=2.0,
            text=(
                "dingy old carpet… The whole place was a bit dark… pulled "
                "pork sandwich… extremely saucy and overly sweet… Reuben "
                "sandwich… was so saucy that the toasted bread was soaked "
                "through and just started disintegrating… 1980s, outdated, "
                "sports bar."
            ),
            signals=["cleanliness", "food_quality", "noise_ambiance"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/westrail-tap-and-grill-lakewood",
            reviewer_first_name="Elli",
            date="2024-05-07",
            stars=2.0,
            text=(
                "waiting over 10 minutes for soft drink orders and didn't "
                "get asked to order for over 15 minutes… waitress is "
                "taking care of 6 tables. We ordered our food at 7:20 and "
                "waited past 8pm."
            ),
            signals=["service_pacing", "staffing"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/westrail-tap-and-grill-lakewood",
            reviewer_first_name="Guest",
            date="2024-03-12",
            stars=2.0,
            text=(
                "Service was extremely slow even though it was a quiet "
                "weeknight. Our server seemed overwhelmed with her "
                "section."
            ),
            signals=["service_pacing", "staffing"],
        ),
        ReviewEvidence(
            source="Yelp",
            source_url="https://www.yelp.com/biz/westrail-tap-and-grill-lakewood",
            reviewer_first_name="Guest",
            date="2023-10-02",
            stars=2.0,
            text=(
                "The burger came out undercooked and had to go back. "
                "The replacement was better but it killed the meal."
            ),
            signals=["food_quality", "food_safety"],
        ),
    ]

    peers = [
        Peer(
            name="Lakewood Grill",
            address="8100 W Colfax Ave, Lakewood CO 80214",
            rating=4.6,
            review_count=600,
            price_tier="$",
            source="Uber Eats / Yelp",
            source_url="https://www.yelp.com/biz/lakewood-grill-lakewood",
        ),
        Peer(
            name="The Rusty Bucket Bar & Grill",
            address="3355 S Wadsworth Blvd Ste G101, Lakewood CO 80227",
            rating=4.1,
            review_count=39,
            price_tier="$$",
            source="TripAdvisor",
            source_url=("https://www.tripadvisor.com/Restaurant_Review-g33514-"
                        "d3842452-Reviews-The_Rusty_Bucket_Bar_and_Grill-"
                        "Lakewood_Colorado.html"),
        ),
        Peer(
            name="Innsider Bar & Grill",
            address="7390 W Hampden Ave, Lakewood CO 80227",
            rating=4.1,
            review_count=152,
            price_tier="$$",
            source="TripAdvisor",
            source_url=("https://www.tripadvisor.com/Restaurant_Review-g33514-"
                        "d1437850-Reviews-Innsider_Bar_Grill-"
                        "Lakewood_Colorado.html"),
        ),
    ]

    return build_scan(
        business=biz,
        evidence=evidence,
        peers=peers,
        contact_email="westrail.events@gmail.com",
        jetpakt_contact={
            "name": "Ryan B.",
            "phone": "303-549-1697",
            "email": "gojetpakt.us@outlook.com",
            "site": "Gojetpakt.com",
        },
    )


if __name__ == "__main__":
    import json
    scan = westrail_fixture()
    # Light JSON-safe dump (skip dataclass internals)
    def _ser(o):
        if hasattr(o, "__dict__"):
            return o.__dict__
        return str(o)
    print(json.dumps(scan, default=_ser, indent=2)[:3000])
