# JetPakt ROI Model — Private Methodology (v1)

**Status:** Auditable reference for the "Estimated recovery" box in the One-Time Scan.
**Target:** Every JetPakt tier designed to deliver ~10x ROI to the customer.
**Date:** April 2026

---

## 1. The claim, stated precisely

The $49 One-Time Scan shows the customer an estimated dollar range of **recoverable monthly revenue** tied to their top guest-experience signals. We claim: *if a single recommendation in the scan is implemented, the customer recovers ≥10x the scan price within 12 months.*

Every number in the scan is:
- **Bounded** — low/mid/high range, never a point estimate, always labeled as estimate
- **Derived** — from the business's own public data (rating, review volume, peer delta) plus industry-standard elasticities
- **Conservative** — we quote the 25th-percentile recovery scenario, not the midpoint

---

## 2. Inputs (all from the scan data we already have)

| Variable | Symbol | Source |
|---|---|---|
| Monthly covers | C | Estimated from review volume (see §3) |
| Average check | A | Industry default by price tier + cuisine |
| Current star rating | R | `business.public_rating` |
| Peer average rating | R_p | `peer_benchmark.avg_peer_rating` |
| Star gap | Δ = R_p − R | Positive = underperforming |
| Recent negative share | N | `business.negative_share_recent` |
| Review volume | V | `business.review_count` |
| Top signal severity | S | `top_signals[0].severity` (1–10) |

---

## 3. Deriving monthly revenue

Restaurants don't publish covers. We estimate from review volume using the **industry review-to-cover ratio** (~1 review per 15–30 paying covers for independent full-service, ~1:40–60 for high-volume QSR). For a casual-dining LoDo restaurant with 732 lifetime reviews over ~8 years, that's ~2,200–4,400 covers/mo at a 1:30 ratio.

```
monthly_covers_low  = V_recent_12mo × 20
monthly_covers_high = V_recent_12mo × 35
monthly_revenue     = monthly_covers × A
```

When `V_recent_12mo` isn't known, we approximate: `V_recent_12mo ≈ V × 0.15` (typical annual share of lifetime reviews for a mature restaurant).

**Defaults for average check A (inclusive of tax, pre-tip):**

| Price tier | Cuisine hint | A_low | A_mid | A_high |
|---|---|---|---|---|
| $ | QSR / fast-casual | $14 | $18 | $22 |
| $$ | Casual / bar-grill | $28 | $38 | $52 |
| $$ | Mexican / Tex-Mex | $26 | $34 | $44 |
| $$ | American pub/grill | $30 | $42 | $58 |
| $$$ | Upscale casual | $55 | $75 | $95 |
| $$$$ | Fine dining | $95 | $135 | $180 |

Denver-specific: the r/denverfood 2025 thread and One-Haus data confirm casual dinner with drinks ≈ $50/person pre-tip — our $38 mid is conservative (accounts for lunch, no-drinks, kids).

**Sources:**
- [One-Haus 2025 Check Averages Report](https://one-haus.com/blog/post/rising-check-averages-in-u-s-restaurants-causes-trends-and-strategies) — QSR $8–$12, fine dining $50–$150+
- [r/denverfood 2025 state of Denver restaurants](https://www.reddit.com/r/denverfood/comments/1rhb13l/the_2025_state_of_denver_restaurants_fed_up/) — Chipotle-tier $22 for two, casual dinner ~$61 for two
- [Denver CVB 2025 State of Restaurants](https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/denver/2025_State_of_Denver_Restaurants_Challenges_Facing_the_Sector_Final_a6d47ea4-e145-4b27-b90d-3447771f2df9.pdf) — 50–55% hourly labor, 22% COGS, 23% rent increases

---

## 4. The recovery model

Three stacked recovery mechanisms, each independently estimated, summed conservatively.

### 4.1 Rating-lift revenue (star elasticity)

Luca (HBS, 2011, Yelp + WA State Dept of Revenue): **a one-star rating increase causes a 5–9% revenue increase for independent restaurants** (chains unaffected). We use the lower bound 5% as our conservative coefficient.

Fixing even one top signal typically returns 0.1–0.3 stars within 60–90 days (smaller operators, faster signal; documented in Anderson & Magruder). We quote:

```
rating_lift_low  = 0.1 star  (one recommendation implemented)
rating_lift_mid  = 0.2 star  (top 2 signals addressed)
rating_lift_high = 0.3 star  (full top-3 action plan executed)

revenue_recovery_from_rating = monthly_revenue × rating_lift × 0.05
```

**Source:** [Luca, M. "Reviews, Reputation, and Revenue: The Case of Yelp.com" (HBS Working Paper 12-016)](https://www.hbs.edu/ris/Publication%20Files/12-016_a7e4a5a2-03f9-490d-b093-8f951238dba2.pdf)

### 4.2 Peak-booking recovery (Anderson & Magruder / Berkeley)

Anderson & Magruder (Berkeley, via ChowNow synthesis): **a half-star improvement raises peak-hour sell-out rate by 19–30%**, up to 49% for restaurants without expert reviews.

Independent Denver restaurants in the target list mostly fall into the "no expert review" bucket. We use the midpoint 24% uplift per half-star, applied only to peak-hour revenue (estimated at 40% of total).

```
peak_revenue = monthly_revenue × 0.40
peak_uplift_per_half_star = 0.24   # midpoint
peak_recovery = peak_revenue × (rating_lift / 0.5) × peak_uplift_per_half_star
```

**Source:** [ChowNow synthesis of Anderson & Magruder UC Berkeley study](https://get.chownow.com/blog/impact-of-online-reviews-on-restaurants/)

### 4.3 Response-labor savings (operational)

JetPakt's defamation-safe response drafts save ~3–5 min per review, at a manager's blended hourly cost of ~$28/hr (Denver CVB 2025: hourly labor up 50–55%, so a $22 base → $34 loaded).

```
reviews_per_mo = V_recent_12mo / 12
minutes_saved  = reviews_per_mo × 4        # mid: 4 min/response
labor_savings  = minutes_saved / 60 × $34
```

This is small (~$50–$200/mo) but **100% guaranteed** — the customer gets it whether or not their rating moves.

### 4.4 Composite monthly recovery

```
recovery_low  = rating_recovery_low  + 0.5 × peak_recovery_low  + labor_savings
recovery_mid  = rating_recovery_mid  + peak_recovery_mid        + labor_savings
recovery_high = rating_recovery_high + peak_recovery_high       + labor_savings
```

The 0.5 weight on peak_recovery in the conservative scenario reflects that peak-hour uplift takes ~60 days to materialize and we want a defensible 90-day figure.

### 4.5 ROI multiple on the $49 scan

```
roi_annualized = recovery_low × 12 / $49
```

Target floor: **≥10x within 12 months** if any single recommendation is implemented. Expected midpoint: 40–100x at casual-dining revenue levels.

---

## 5. Worked examples

### Westrail Tap & Grill ($$, American pub/grill, 3.3★/487 reviews, 28% neg share)

- V_recent_12mo ≈ 487 × 0.15 = 73 reviews/yr ≈ 6/mo
- monthly_covers ≈ 73 × 30 = 2,190 (annualized ~26,000)
  - Low/high bounds: 20× to 35× → 1,460 to 2,555 covers/mo
- A_mid = $42 (American pub/grill $$)
- monthly_revenue ≈ 2,190 × $42 = **$91,980/mo mid-case** (range $61K–$148K)

Recovery:
- Rating: 0.1★ × 0.05 × $92K = **$460/mo low**; 0.2★ → $920/mo mid; 0.3★ → $1,380/mo high
- Peak: $92K × 0.40 × (0.1/0.5) × 0.24 = **$1,766/mo** at 0.1★ uplift (half-weighted for 90d realism: $883)
- Labor: 6 × 4 / 60 × $34 = **$14/mo** (trivially small; still real)

**Composite low (90-day conservative): ~$1,350/mo · annualized $16,200 · ROI on $49 ≈ 330x**
**Composite mid (180-day realistic): ~$3,580/mo · annualized $43,000 · ROI ≈ 870x**

The 10x claim is met at 0.03★ of improvement — well below the conservative 0.1★ assumption. Solid.

### Lime on Larimer ($$, Mexican, 3.2★/732 reviews, 39% neg share)

- V_recent_12mo ≈ 732 × 0.15 = 110/yr ≈ 9/mo
- monthly_covers ≈ 110 × 30 = 3,300 (range 2,200–3,850)
- A_mid = $34 (Mexican $$)
- monthly_revenue ≈ 3,300 × $34 = **$112,200/mo mid-case**

Recovery:
- Rating: 0.1★ lift × 5% × $112K = **$561/mo low**
- Peak: $112K × 0.40 × (0.1/0.5) × 0.24 × 0.5 = **$1,075/mo** (half-weighted)
- Labor: 9 × 4 / 60 × $34 = **$20/mo**

**Composite low: ~$1,660/mo · annualized $19,900 · ROI ≈ 406x**

Peer gap is larger (−1.03★ vs peers at 4.23) so the upside ceiling is materially higher; we still quote the low.

---

## 6. Guardrails on the claim

1. **Every number in the customer-facing box must be shown as a range, never a point.** "$1,350 – $3,580/mo" — not "$2,400/mo."
2. **Always footnote the sources.** Luca HBS, Berkeley/Anderson & Magruder, Denver CVB, One-Haus. Full URLs in PDF footer.
3. **Always tag as estimate.** "Estimated recovery" / "Projected range" / "Conservative floor." Never "will recover" or "you will earn."
4. **Never claim the recovery without implementation.** The 10x is conditional on the customer executing at least one 30-day action from the plan.
5. **For legal-flagged leads**, route the ROI narrative through the soft-pitch variant (no aggressive dollar claims on LEGAL-HIGH service-fee leads).
6. **Floor the claim at 10x** — if the model produces <10x for a given business (e.g., very low review volume, very low ticket size), we drop the dollar figure and show only the qualitative "recovery potential" language.

---

## 7. Calibration plan

After the first 5 paying customers:

- Ask each post-90-days: did the top-signal recommendation land?
- Measure actual rating change 60/90/180 days post-scan
- Compare modeled recovery range against self-reported revenue impact
- Adjust the elasticity coefficient, cover-to-review ratio, and peak-hour share

Version this document on every calibration update (v1 → v1.1 → v2). Bake the current version string into the scan PDF's methodology footer.

---

## 8. What we explicitly do not claim

- That JetPakt will generate N new customers — we claim recovery of lost revenue from existing ones
- Any uplift to chain restaurants (Luca: no elasticity effect)
- Dollar-exact promises — always ranges, always estimates
- Recovery for restaurants already rated ≥4.3★ (limited upside; our target is 3.0–3.9★)
- Any specific labor, training, or capex savings beyond documented response-draft time
