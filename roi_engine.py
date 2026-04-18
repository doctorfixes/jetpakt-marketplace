"""
JetPakt ROI engine — deterministic recovery estimator.

Implements the model from docs/ROI_MODEL.md v1.

The estimator takes a Business + its peer_benchmark and returns a low/mid/high
monthly recovery range, annualized value, an ROI multiple against the $49
One-Time Scan price, and the citations used.

All defaults are conservative (25th-percentile scenario):
  - 5% revenue lift per star (Luca HBS lower bound)
  - 0.1 / 0.2 / 0.3 star lift for low / mid / high scenarios
  - Peak recovery half-weighted in the 90-day "low" number
  - Cover-to-review midpoint 30

If the model cannot justify the ≥10x floor for a business (tiny review volume,
etc.) we emit `qualify=False` and the caller is expected to drop the dollar
figure and show qualitative language only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scan_engine import Business  # type: ignore

# --- Model constants (all traceable to ROI_MODEL.md) ------------------------

SCAN_PRICE_USD = 49.0
RECENT_REVIEW_SHARE_OF_LIFETIME = 0.15       # V_recent_12mo ≈ V × 0.15
COVERS_PER_REVIEW_LOW = 20                   # industry 1:20–1:35 for full-service
COVERS_PER_REVIEW_MID = 30
COVERS_PER_REVIEW_HIGH = 35
STAR_ELASTICITY = 0.05                        # Luca HBS conservative lower bound
PEAK_REVENUE_SHARE = 0.40                     # dinner / peak share of monthly sales
PEAK_UPLIFT_PER_HALF_STAR = 0.24              # Anderson & Magruder midpoint
PEAK_LOW_WEIGHT = 0.5                         # half-weighted for 90-day realism
RATING_LIFT_LOW = 0.10
RATING_LIFT_MID = 0.20
RATING_LIFT_HIGH = 0.30
MANAGER_LOADED_HOURLY_USD = 34.0              # Denver CVB 2025 hourly + load
MINUTES_SAVED_PER_RESPONSE = 4.0
ROI_FLOOR_MULTIPLE = 10.0                     # 10x target — else qualitative only

# Price tier × cuisine hint → (A_low, A_mid, A_high)
# Source: One-Haus 2025 / r/denverfood 2025 / Denver CVB
CHECK_AVERAGE_TABLE: dict[tuple[str, str], tuple[float, float, float]] = {
    ("$",   "qsr"):          (14.0, 18.0, 22.0),
    ("$",   "fast_casual"):  (14.0, 18.0, 22.0),
    ("$$",  "casual"):       (28.0, 38.0, 52.0),
    ("$$",  "mexican"):      (26.0, 34.0, 44.0),
    ("$$",  "american"):     (30.0, 42.0, 58.0),
    ("$$",  "pub_grill"):    (30.0, 42.0, 58.0),
    ("$$$", "upscale"):      (55.0, 75.0, 95.0),
    ("$$$$", "fine_dining"): (95.0, 135.0, 180.0),
}

# Fallback check averages when cuisine is unknown
DEFAULT_CHECK_BY_TIER: dict[str, tuple[float, float, float]] = {
    "$":    (14.0, 18.0, 22.0),
    "$$":   (28.0, 38.0, 52.0),
    "$$$":  (55.0, 75.0, 95.0),
    "$$$$": (95.0, 135.0, 180.0),
}

CITATIONS: dict[str, str] = {
    "luca_hbs":
        "https://www.hbs.edu/ris/Publication%20Files/12-016_a7e4a5a2-03f9-490d-b093-8f951238dba2.pdf",
    "anderson_magruder":
        "https://get.chownow.com/blog/impact-of-online-reviews-on-restaurants/",
    "one_haus":
        "https://one-haus.com/blog/post/rising-check-averages-in-u-s-restaurants-causes-trends-and-strategies",
    "denver_cvb":
        "https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/denver/"
        "2025_State_of_Denver_Restaurants_Challenges_Facing_the_Sector_Final_"
        "a6d47ea4-e145-4b27-b90d-3447771f2df9.pdf",
}


# --- Types ------------------------------------------------------------------

@dataclass
class RecoveryEstimate:
    """The ROI box payload the PDF renders."""

    qualify: bool                          # False → drop dollars, use qualitative only
    monthly_low: float                     # conservative 90-day figure
    monthly_mid: float                     # realistic 180-day figure
    monthly_high: float                    # full-action ceiling
    annualized_low: float                  # monthly_low × 12
    roi_multiple_low: float                # annualized_low / $49
    roi_multiple_mid: float
    assumptions: dict[str, Any] = field(default_factory=dict)
    citations: list[dict[str, str]] = field(default_factory=list)
    version: str = "v1"


# --- Cuisine inference ------------------------------------------------------

_MEXICAN_HINTS = ("mex", "taco", "cantina", "taqueria", "burrito", "cocina", "lime")
_PUB_HINTS = ("tap", "grill", "pub", "tavern", "bar", "brew")
_QSR_HINTS = ("fast", "quick", "qsr")


def infer_cuisine(business: Business, signals: list[dict] | None = None) -> str:
    """Best-guess cuisine key for CHECK_AVERAGE_TABLE lookup.

    Order of precedence:
      1. explicit tier $ → qsr
      2. explicit tier $$$ → upscale; $$$$ → fine_dining
      3. name heuristics
      4. fall back to 'casual'
    """
    tier = (business.price_tier or "$$").strip()
    name = (business.name or "").lower()

    if tier == "$":
        return "qsr"
    if tier == "$$$":
        return "upscale"
    if tier == "$$$$":
        return "fine_dining"

    if any(h in name for h in _MEXICAN_HINTS):
        return "mexican"
    if any(h in name for h in _PUB_HINTS):
        return "american"
    if any(h in name for h in _QSR_HINTS):
        return "qsr"
    return "casual"


def check_average_range(business: Business,
                        cuisine_hint: str | None = None) -> tuple[float, float, float]:
    """Look up (A_low, A_mid, A_high) for a business."""
    tier = (business.price_tier or "$$").strip()
    cuisine = cuisine_hint or infer_cuisine(business)
    key = (tier, cuisine)
    if key in CHECK_AVERAGE_TABLE:
        return CHECK_AVERAGE_TABLE[key]
    return DEFAULT_CHECK_BY_TIER.get(tier, DEFAULT_CHECK_BY_TIER["$$"])


# --- Core model -------------------------------------------------------------

def _monthly_revenue(business: Business,
                     cuisine_hint: str | None = None
                     ) -> tuple[float, float, float, dict[str, Any]]:
    """
    Estimate monthly revenue low/mid/high from review volume + avg check.

    Returns (low, mid, high, internals) where internals exposes the
    reviews-per-month and covers-per-month used, so the PDF can footnote them.
    """
    v_recent = max(business.review_count * RECENT_REVIEW_SHARE_OF_LIFETIME, 0.0)
    reviews_per_month = v_recent / 12.0

    # Per ROI_MODEL.md §3: monthly_covers = V_recent_12mo × ratio.
    # The ratio here (20 / 30 / 35) is calibrated so it already represents
    # covers-per-month-per-annual-review — i.e. it bakes in the /12 implicitly.
    # See worked examples for Westrail and Lime in the methodology doc.
    covers_low = v_recent * COVERS_PER_REVIEW_LOW
    covers_mid = v_recent * COVERS_PER_REVIEW_MID
    covers_high = v_recent * COVERS_PER_REVIEW_HIGH

    a_low, a_mid, a_high = check_average_range(business, cuisine_hint)

    rev_low = covers_low * a_low
    rev_mid = covers_mid * a_mid
    rev_high = covers_high * a_high

    return rev_low, rev_mid, rev_high, {
        "reviews_per_month": round(reviews_per_month, 1),
        "covers_per_month_mid": round(covers_mid),
        "avg_check_mid": round(a_mid, 2),
        "v_recent_12mo": round(v_recent, 1),
    }


def _rating_lift_revenue(monthly_revenue: float, rating_lift: float) -> float:
    """5% revenue per star × fractional star lift."""
    return monthly_revenue * rating_lift * STAR_ELASTICITY


def _peak_uplift_revenue(monthly_revenue: float, rating_lift: float) -> float:
    """Anderson & Magruder peak-hour booking uplift."""
    peak_rev = monthly_revenue * PEAK_REVENUE_SHARE
    return peak_rev * (rating_lift / 0.5) * PEAK_UPLIFT_PER_HALF_STAR


def _labor_savings(reviews_per_month: float) -> float:
    minutes = reviews_per_month * MINUTES_SAVED_PER_RESPONSE
    return (minutes / 60.0) * MANAGER_LOADED_HOURLY_USD


def estimate_recovery(business: Business,
                      peer_benchmark: dict[str, Any] | None = None,
                      cuisine_hint: str | None = None) -> RecoveryEstimate:
    """
    Deterministic ROI estimator.

    Inputs:
      business        — scan_engine.Business
      peer_benchmark  — optional {'avg_peer_rating', 'delta_vs_peers'}; used
                        only to inform which lift scenario is realistic. Does
                        not change the numerical model in v1 (the model is
                        conservative by default). Kept in the signature so v2
                        can shrink/expand lift assumptions using peer delta.
      cuisine_hint    — optional override for check-average lookup

    Output: RecoveryEstimate — always returned; `qualify=False` means the
    caller must suppress the dollar figures.
    """
    rev_low, rev_mid, rev_high, internals = _monthly_revenue(business, cuisine_hint)

    # Per ROI_MODEL.md §4: low/mid/high are *scenario* differences (how much
    # of the action plan the operator executes), NOT revenue-range differences.
    # Compute all three against the mid revenue estimate; the revenue range is
    # informational only and surfaced in `assumptions` for the footnote.
    rating_low = _rating_lift_revenue(rev_mid, RATING_LIFT_LOW)
    rating_mid = _rating_lift_revenue(rev_mid, RATING_LIFT_MID)
    rating_high = _rating_lift_revenue(rev_mid, RATING_LIFT_HIGH)

    peak_low_full = _peak_uplift_revenue(rev_mid, RATING_LIFT_LOW)
    peak_mid_full = _peak_uplift_revenue(rev_mid, RATING_LIFT_MID)
    peak_high_full = _peak_uplift_revenue(rev_mid, RATING_LIFT_HIGH)

    # Conservative low half-weights peak to hold up at 90 days
    peak_low = peak_low_full * PEAK_LOW_WEIGHT

    labor = _labor_savings(internals["reviews_per_month"])

    monthly_low = rating_low + peak_low + labor
    monthly_mid = rating_mid + peak_mid_full + labor
    monthly_high = rating_high + peak_high_full + labor

    annualized_low = monthly_low * 12.0
    annualized_mid = monthly_mid * 12.0

    roi_low = annualized_low / SCAN_PRICE_USD if SCAN_PRICE_USD else 0.0
    roi_mid = annualized_mid / SCAN_PRICE_USD if SCAN_PRICE_USD else 0.0

    qualify = roi_low >= ROI_FLOOR_MULTIPLE and monthly_low >= 50.0

    # Round money figures to nearest $10 for defensibility; never quote to the dollar.
    def _round10(x: float) -> float:
        return round(x / 10.0) * 10.0

    # Avg peer delta passed into assumptions for the PDF footnote
    delta = None
    if peer_benchmark:
        delta = peer_benchmark.get("delta_vs_peers")

    assumptions: dict[str, Any] = {
        "v_recent_12mo": internals["v_recent_12mo"],
        "reviews_per_month": internals["reviews_per_month"],
        "covers_per_month_mid": internals["covers_per_month_mid"],
        "avg_check_mid": internals["avg_check_mid"],
        "monthly_revenue_mid": round(rev_mid),
        "monthly_revenue_low": round(rev_low),
        "monthly_revenue_high": round(rev_high),
        "price_tier": business.price_tier,
        "cuisine_hint": cuisine_hint or infer_cuisine(business),
        "star_elasticity": STAR_ELASTICITY,
        "peak_uplift_per_half_star": PEAK_UPLIFT_PER_HALF_STAR,
        "peak_revenue_share": PEAK_REVENUE_SHARE,
        "rating_lift_low_mid_high": [RATING_LIFT_LOW, RATING_LIFT_MID, RATING_LIFT_HIGH],
        "scan_price_usd": SCAN_PRICE_USD,
        "roi_floor_multiple": ROI_FLOOR_MULTIPLE,
        "peer_delta": delta,
    }

    citations = [
        {
            "label": "Luca, M. — Reviews, Reputation, and Revenue (HBS 12-016)",
            "detail": "5–9% revenue per star, independent restaurants; we use 5% lower bound",
            "url": CITATIONS["luca_hbs"],
        },
        {
            "label": "Anderson & Magruder (UC Berkeley) via ChowNow synthesis",
            "detail": "24% peak-hour uplift per half-star midpoint",
            "url": CITATIONS["anderson_magruder"],
        },
        {
            "label": "One-Haus 2025 Check Averages",
            "detail": "QSR $8–$12 · casual $28–$52 · upscale $55–$95+",
            "url": CITATIONS["one_haus"],
        },
        {
            "label": "Denver CVB 2025 State of Restaurants",
            "detail": "Hourly labor 50–55%, loaded manager wage ~$34/hr",
            "url": CITATIONS["denver_cvb"],
        },
    ]

    return RecoveryEstimate(
        qualify=qualify,
        monthly_low=_round10(monthly_low),
        monthly_mid=_round10(monthly_mid),
        monthly_high=_round10(monthly_high),
        annualized_low=round(annualized_low),
        roi_multiple_low=round(roi_low),
        roi_multiple_mid=round(roi_mid),
        assumptions=assumptions,
        citations=citations,
        version="v1",
    )


# --- Convenience: dict form for JSON logs / PDF payload ---------------------

def recovery_to_dict(rec: RecoveryEstimate) -> dict[str, Any]:
    return {
        "qualify": rec.qualify,
        "monthly_low": rec.monthly_low,
        "monthly_mid": rec.monthly_mid,
        "monthly_high": rec.monthly_high,
        "annualized_low": rec.annualized_low,
        "roi_multiple_low": rec.roi_multiple_low,
        "roi_multiple_mid": rec.roi_multiple_mid,
        "assumptions": rec.assumptions,
        "citations": rec.citations,
        "version": rec.version,
    }
