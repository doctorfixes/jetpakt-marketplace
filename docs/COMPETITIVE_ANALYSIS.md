# JetPakt Competitive Analysis v1 — Where the Category Breaks, and the Product That Exploits It

> Operating principle: **design the product to provide 10x ROI for the customer**. The competitive map below shows why that floor is defensible — no incumbent publishes one. This doc maps the category's structural weaknesses to JetPakt's already-shipped assets, then proposes the minimum product restructure that converts those assets into a durable moat.

---

## 1. Executive summary — the category is a dashboard arms race that left six gaps

Twelve competitors researched in April 2026 ([full matrix §2](#2-the-12-competitor-matrix)). The category has consolidated around a single playbook: aggregate review sites, add an AI responder, charge per location, quote on the top end. That playbook leaves six structural gaps JetPakt can occupy today without new engineering:

1. **Nobody publishes a defensible ROI model.** Every competitor claims a number — "4x reviews" ([TrustYou](https://www.trustyou.com/blog/insights/ratings-impact-revenue/)), "128% review increase" ([Birdeye](https://birdeye.com/blog/restaurant-reputation-management/)), "192% ROI" ([SOCi](https://www.soci.ai/industries/restaurants/)), "18-24x feedback" ([Ovation](https://ovationup.com)) — none cite the math. JetPakt already ships a Luca-elasticity grounded ROI range with source URLs ([`docs/ROI_MODEL.md`](../docs/ROI_MODEL.md)).
2. **Only two competitors address FTC/defamation risk — both enterprise-only.** [SOCi](https://www.soci.ai/industries/restaurants/) and [Chatmeter](https://www.chatmeter.com/industries/restaurants/) mention legal escalation at $16k-$62k/yr floors. Everyone under $500/mo, including the $19/mo auto-responders, is silent on the [FTC 2024 Final Rule ($51,744/violation)](https://www.wilmerhale.com/-/media/files/shared_content/editorial/publications/wh_publications/client_alert_pdfs/20241009-ftc-finalizes-rule-banning-fake-reviews.pdf). [Ovation has user-noted legal concerns about its solicitation mechanics](https://www.capterra.com/p/181479/Ovation/).
3. **Per-location pricing punishes independents.** [Birdeye at $299/loc](https://birdeye.com/hospitality/), [Reputation.com at $80-150/loc](https://reputation.com/pricing), [ReviewTrackers at $89/loc](https://www.reviewtrackers.com/plans/), [Grade.us at $110/seat](https://www.grade.us/home/plans/) — every group-friendly tool scales against the operator. JetPakt's Tier 4 flat multi-location price ([`PRICING_MODEL.md §3`](./PRICING_MODEL.md)) is built for this gap.
4. **Opaque pricing above the floor is universal.** Ten of twelve competitors force a "contact sales" above entry. Only [TrustYou](https://www.trustyou.com/pricing/cxp/) and [Grade.us](https://www.grade.us/home/plans/) publish their ladder end-to-end.
5. **The AI auto-response race is a defamation trap.** [Podium](https://podium.com/product/reviews/), [Birdeye](https://birdeye.com/blog/restaurant-reputation-management/), [SOCi](https://www.soci.ai/industries/restaurants/), [NiceJob Pro](https://get.nicejob.com/pricing), [Ovation](https://ovationup.com), [Chatmeter](https://www.chatmeter.com/pricing/), [ReviewTrackers](https://www.reviewtrackers.com/reputation-management-software/), even [$19/mo indie SaaS](https://www.reddit.com/r/AI_Agents/comments/1s8ekd0/would_you_pay_19month_for_a_tool_that_autoreplies/) — all sell auto-generated replies as the headline feature. None gate them behind human review. JetPakt's guardrail ([`GUARDRAILS.md`](./GUARDRAILS.md) — drafts-over-auto-send, per-row approval, 17 drafts in Outlook never recreated) inverts that posture.
6. **Nobody offers hospitality-specific severity.** Generic sentiment treats a billing-disputes 1-star the same as a noise-ambiance 1-star — the economic impact differs by an order of magnitude. JetPakt's [`SIGNAL_LIBRARY`](../scan_engine.py) (10 hospitality-specific signals: billing_disputes, cleanliness, food_quality, food_safety, noise_ambiance, pricing_value, server_attitude, service_fee_transparency, service_pacing, staffing) is the category's only evidence-tied, operator-legible taxonomy.

**The thesis:** The category is built for chains buying dashboards. The underserved market is the independent or small-group operator who needs an evidence-backed, economically honest, legally-safe shortlist — delivered as a deliverable, not a login. JetPakt already has every component. The restructure below turns components into modules an operator can buy, compound, and defend.

---

## 2. The 12-competitor matrix

Pricing and features verified April 2026 from vendor sites, G2, Capterra, and third-party review analyses.

| Competitor | Target | Entry | Top | Pricing Model | Sites Covered | AI Auto-Response | Human-in-Loop | Legal/FTC Awareness | Published ROI | Public Pricing | Single-Site Friendly |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **[Google Business Profile](https://business.google.com/us/business-profile/restaurants/)** | All | Free | Free | Free | Google only | No | N/A | Policy flags only | None | Full | Yes |
| **[TrustYou CXP](https://www.trustyou.com/pricing/cxp/)** | Hospitality | $75/prop | $350 | Per-property/yr | 200+ | Yes (ResponseAI) | Optional | GDPR/CCPA only | Generic "4x speed" | Full | Yes |
| **[Yelp for Business](https://business.yelp.com/products/)** | Restaurants | $99-150 | $1,500+ | CPC + flat | Yelp primary | No | Yes | Policy only | "40:1 ROAS" case | Partial | Yes |
| **[Reputation.com](https://reputation.com/pricing)** | Multi-loc chains | $80/loc | $150+/loc | Per-location | 250+ | AI insights only | Templates | None | Generic | Partial | No (punished) |
| **[Grade.us](https://www.grade.us/home/plans/)** | Agencies | $110/seat | $2,500 | Per-seat | 100+ | No | N/A | Google-compliant kiosk | Agency-margin calc | Full | Yes (Solo) |
| **[Podium](https://podium.com/product/reviews/)** | Local/SMB | $249-399 | $599+ | Quote + add-ons | 20+ | Yes | Optional | None | Generic "2x reviews" | Opaque | No (floor too high) |
| **[ReviewTrackers](https://www.reviewtrackers.com/plans/)** | Multi-loc | $89/loc | Custom | Per-loc + add-ons | 100+ | Yes (Smart Responses) | Optional | None | Generic | Partial | Partial |
| **[Birdeye](https://birdeye.com/hospitality/)** | Multi-loc | $299/loc | $449+/loc | Per-location | 150+ | Yes (Response Agent) | Optional | None | "128% / 71%" | Opaque | No (punished) |
| **[SOCi](https://www.soci.ai/industries/restaurants/)** | Enterprise | ~$1,900/mo | $5,200+/mo | Custom enterprise | Google/Yelp/delivery | Yes (Genius Agent) | Required on sensitive | **Yes — legal/safety escalation** | "192% ROI" (vendor) | None | No |
| **[NiceJob](https://get.nicejob.com/pricing)** | SMB | $75 | $125 | Flat + custom multi | 10+ | Yes (Pro) | Optional | None | Generic "4x" | Partial | Yes |
| **[Ovation Up](https://ovationup.com)** | Multi-unit | $99/user | Custom | Per-user/location | 50+ dirs | Yes (suggested replies) | Optional | **User-reported solicitation concerns** ([Capterra](https://www.capterra.com/p/181479/Ovation/)) | "18-24x feedback" | Opaque | Yes (adapts) |
| **[Chatmeter](https://www.chatmeter.com/pricing/)** | Multi-loc enterprise | ~$1,333/mo | $3,500/mo | Per-loc annual | 85+ | Yes (Pulse AI) | Optional | **Yes — discrimination/safety alerts, HIPAA** | Generic | Opaque | No |

See [`competitor_matrix.csv`](../../wide/research_results_mo3yo46y.csv) for the full 17-field dataset including source URLs for every cell.

---

## 3. Category-wide structural weaknesses (the gaps to monetize)

Seven patterns emerged consistently across the twelve products. Each is a gap JetPakt already has an asset for.

### 3.1 The ROI black hole
Claims without citations: "4x reviews," "128% increase," "192% ROI," "18-24x feedback." Not one vendor shows the elasticity curve, the peer delta, or the revenue math. A buyer who asks "show me the $1,360/mo" gets a case study, not a formula. **JetPakt asset:** [`roi_engine.py`](../roi_engine.py) + [`docs/ROI_MODEL.md`](./ROI_MODEL.md) — Luca-elasticity × peak-hour uplift × local check averages, range not point estimate, every input cited.

### 3.2 Legal/FTC silence under $500/mo
The [FTC Final Rule effective October 2024](https://www.wilmerhale.com/-/media/files/shared_content/editorial/publications/wh_publications/client_alert_pdfs/20241009-ftc-finalizes-rule-banning-fake-reviews.pdf) imposes $51,744 per violation for fake reviews, incentivized reviews without disclosure, and insider reviews. [Google prohibits gating and incentivized reviews](https://support.google.com/contributionpolicy/answer/7400114?hl=en). [Yelp filters solicited reviews via their Recommendation Software](https://www.yelp-support.com/article/Don-t-Ask-for-Reviews?l=en_US). None of the sub-$500/mo competitors mention any of this. The $19/mo indie tools suggest language that could be actionable. **JetPakt asset:** [`scan_pdf.py _review_growth_box()`](../scan_pdf.py) red AVOID callout citing all three policies + defamation-safe response templates in [`scan_engine.py`](../scan_engine.py).

### 3.3 Per-location scaling punishes the operators who need help most
The small-group Denver operator with 2-3 sites pays the worst marginal rate on Birdeye ($299/loc × 3 = $897/mo), Reputation.com ($80-150/loc), and ReviewTrackers ($89/loc + add-ons). The independents who would benefit most from the tool pay multiples of what a 500-location chain pays per site. **JetPakt asset:** [`PRICING_MODEL.md §3 Tier 4`](./PRICING_MODEL.md) — flat $149/mo/loc for multi-location, explicitly designed to invert this dynamic.

### 3.4 Opacity above the floor is the universal sales tactic
Ten of twelve competitors force "contact sales" above the entry tier. This is friction the buyer pays for: demo scheduling, vendor pressure, unbundled add-ons, annual contracts. The MarginEdge precedent (all-in-flat, publicly priced) proves operators prefer a number. **JetPakt asset:** [`PRICING_MODEL.md`](./PRICING_MODEL.md) publishes every tier including the $24k/yr Enterprise floor — no quote dance.

### 3.5 AI auto-response is a defamation-generating machine sold as a feature
Podium's, Birdeye's, SOCi's, Ovation's AI response agents are the headline features. None gate those responses behind a human review of the specific guest complaint. In a market where a 1-star from a real guest can become a lawsuit if mishandled (or a $51,744 FTC exposure if a counter-review is orchestrated), auto-send is negligence sold as productivity. **JetPakt asset:** [`GUARDRAILS.md`](./GUARDRAILS.md) — drafts-over-auto-send, per-row approval, 17 drafts already live in Outlook; the guardrail is the product.

### 3.6 Generic sentiment ignores hospitality economics
No competitor's taxonomy distinguishes "billing_disputes" from "noise_ambiance" — the former is a billing-audit remediation costing hours; the latter is a capex decision costing months. Aggregating them into a single "sentiment score" hides the severity structure an operator needs to prioritize. **JetPakt asset:** 10-signal [`SIGNAL_LIBRARY`](../scan_engine.py) with evidence-tied severity scores and signal-specific recovery paths.

### 3.7 Nobody ties outcomes to pricing
Every pricing model is subscription or per-seat. No competitor ties their fee to the recovered revenue they delivered. **JetPakt asset:** [`PRICING_MODEL.md §3 Tier 5`](./PRICING_MODEL.md) — $1,200/mo flat OR $99 + 5% of recovered revenue, whichever is lower. Nobody else has skin in the game.

---

## 4. JetPakt defensible strengths mapped to competitor gaps

Every strength below is already shipped and validated in this repo. The restructure in §5 turns them into named, sellable modules.

| JetPakt asset (shipped) | Competitor gap | Evidence |
|---|---|---|
| Evidence-tied severity scoring | Generic sentiment aggregation | [`scan_engine.py`](../scan_engine.py) SIGNAL_LIBRARY + 3-quote floor per signal |
| Luca-elasticity ROI engine with range output | Un-cited "Nx" revenue claims | [`roi_engine.py`](../roi_engine.py) + [`docs/ROI_MODEL.md`](./ROI_MODEL.md) + 5 scans producing 332x-5,790x validated ranges |
| Defamation-safe response templates | Auto-response defamation exposure | [`scan_engine.py`](../scan_engine.py) response drafts + [`GUARDRAILS.md`](./GUARDRAILS.md) human-in-loop |
| Review-growth module with Yelp-negative guidance | Universal silence on platform rules | [`scan_pdf.py _review_growth_box()`](../scan_pdf.py) — 5 tactics + red AVOID callout citing FTC/Google/Yelp |
| Hospitality-first PDF deliverable | SaaS-dashboard-as-product | Instrument Serif + Inter + DM Sans, #20808D / #F7F6F2, 9-10 page consulting-style scan |
| Human-in-the-loop guardrail (17 Outlook drafts, drafts-never-sent) | Auto-send negligence | [`GUARDRAILS.md`](./GUARDRAILS.md) |
| Performance-based pricing option | No skin-in-the-game competitors | [`PRICING_MODEL.md §3 Tier 5`](./PRICING_MODEL.md) $99+5% option |
| Public, sequential pricing ladder | Opacity above floor | [`PRICING_MODEL.md`](./PRICING_MODEL.md) Tier 0-6 all published |

Every row above is a one-sentence answer to "why you, not [Birdeye/Podium/SOCi]?"

---

## 5. Proposed product restructure — six named modules the operator buys, compounds, and defends

The current product is a single PDF scan plus a Python engine. That flat structure leaves value on the table — an operator can't see which part to buy, upgrade, or recommend. The restructure below keeps the same code but renames, repackages, and wires it into six modules that map 1:1 to the gaps in §3. Each module is already 80%+ shipped; the work is naming, sequencing, and one new artifact per module.

### 5.0 Framework spine — the Restaurant Operating System (ROS)

As of v1.1, every module below sits on a shared framework spine: the five-pillar **Restaurant Operating System** (Production / Service / Sales / Operations / Management), documented in full at [docs/ROS_FRAMEWORK.md](ROS_FRAMEWORK.md). The ROS framework contributes four things to the restructure:

- **Pillar vocabulary.** Every signal now carries a pillar + 24-case reference. "Service pacing severity 7.4" becomes "Service-pillar drift, cases I06 + I01."
- **Principle-guided actions.** Every PLAYBOOK action can cite 1–2 of the 49 operating principles (Theory of Constraints, Six Sigma, Pareto, Game Theory, etc.) — turning restaurant folklore into engineered prescriptions.
- **Quantified case benchmarks.** Each of the 24 ROS cases ships a simulated weekly-revenue-lift range with 95% CIs. JetPakt's recovery math now has a second, independent anchor.
- **Cadence alignment.** The ROS Weekly Cadence Master (daily line checks → weekly prime-cost → monthly menu engineering → quarterly standards audit) maps cleanly onto JetPakt's pricing tiers — see PRICING_MODEL.md §3 updates.

The six modules below inherit this spine. None are replaced; all are sharpened by it.

### 5.1 **Scan Core** — the deliverable everyone else is missing
- Already shipped. The PDF scan with severity + ROI + response drafts + review-growth + 30/60/90 plan.
- **What changes:** rename internally to "Scan Core" so every other module references it. Make it the anchor of every tier.
- **Monetized in:** Tier 1 ($49) and bundled into Tier 2+ monthly re-scans.
- **Fills gap:** 3.1 (ROI), 3.6 (severity), 3.7 (deliverable-as-product).

### 5.2 **Evidence Graph** — the compounding moat nobody else can build
- **New lightweight module.** Every scan writes its signal-severity-quote tuples into a JSONL store keyed on `(business_id, signal, scan_date)`. Already 70% shipped — scans write JSON; just need a central append log.
- Over time, a returning client sees drift ("service_pacing climbed from 5.2 → 7.1 in 60 days") with the exact quote trail that caused the climb.
- **Why it's defensible:** a competitor cannot replicate a Denver operator's 12-month evidence graph without 12 months. First-mover lock-in per customer.
- **Monetized in:** Tier 2 ($79/mo) drift alerts; Tier 3 ($179/mo) weekly trend report.
- **Fills gap:** 3.1 (compound ROI proof), 3.6 (hospitality-specific trend).
- **Build cost:** ~1 day — JSONL appender + drift-delta helper in `scan_engine.py`.

### 5.3 **Legal Shield** — the $16k/yr SOCi feature at $79/mo
- **Already shipped** as the defamation-safe templates + FTC red-callout + [`GUARDRAILS.md`](./GUARDRAILS.md). Needs one artifact: a per-scan 1-page "Legal Posture Audit" listing which platform rules apply to the operator's current review patterns (Yelp filter exposure, Google policy gates, FTC Rule touchpoints) with citations.
- **Why it's defensible:** SOCi and Chatmeter charge $16k-$62k/yr for this. Offering it at $79/mo is a 20x price advantage on a feature that is pure policy-reading expertise.
- **Monetized in:** Tier 2 baseline; Tier 3 adds quarterly lawyer-review option (`PRICING_MODEL.md` add-on $89).
- **Fills gap:** 3.2, 3.5.
- **Build cost:** ~4 hours — assemble existing citations into a reusable 1-pager template in `scan_pdf.py`.

### 5.4 **Principle-Guided Playbook** — 30/60/90 ranked by recovery, cited by principle

*Previously "Plain-English Playbook." Renamed in v1.1 to reflect the ROS integration — every action now cites the operating principle that justifies it.*

- **Already shipped** as the 30/60/90 plan section. Needs one enhancement: sort items by recovery-$/effort ratio, not by severity rank. Today an operator sees "fix service_fee_transparency first" because severity is 10.0; they should see "fix it first because it recovers $2,410-11,950/mo for 2 hours of menu-edit work."
- **Why it's defensible:** every competitor's output is a dashboard, not a ranked to-do. An operator at 10pm needs the list, not the login.
- **Monetized in:** Scan Core (Tier 1+); the enhancement makes every tier stickier.
- **Fills gap:** 3.6, 3.7.
- **Build cost:** ~2 hours — add `recovery_per_hour` field to signal metadata, re-sort `_plan_box`.

### 5.5 **Operator Co-pilot** — human Ryan + AI, never auto-send
- **Already shipped** as the 17 Outlook drafts + human-in-loop. Formalize as a named module with monthly call (Tier 3) and retainer (Tier 5).
- **Why it's defensible:** this is the direct inversion of the competitor auto-response race. The sales line is *"we write the draft, you read the guest's words, you hit send"* — which doubles as the legal shield pitch.
- **Monetized in:** Tier 3 ($179/mo, 30-min call), Tier 5 retainer ($1,200/mo or $99+5%).
- **Fills gap:** 3.2, 3.5, 3.7.
- **Build cost:** zero — already shipped. Needs only a one-page landing describing the posture.

### 5.6 **Peer Pulse + Denver Severity Index** — the neighborhood-specific benchmarking nobody owns
- **Partially shipped.** Each scan pulls 2-3 hyperlocal peers (Westrail → Dairy Block, Casa Bonita → Lakewood Mexican, Hampton Social → LoDo brunch, Hey Kiddo → Highland casual). The missing artifact is a public-facing **Denver Severity Index** — aggregated (de-identified) severity scores by signal and neighborhood, updated monthly.
- **Why it's defensible:** (a) SEO moat — ranks for "Denver restaurant review trends" queries; (b) sales proof — every scan says *"you're 2.3 points above the LoDo median on service_pacing, here's the public index"*; (c) operator-to-operator word-of-mouth; (d) no national competitor can replicate without 12 months of local scans.
- **Monetized in:** free public page drives Tier 0-1 conversion; private Peer Pulse (3 specific peers refreshed monthly) is Tier 3 feature.
- **Fills gap:** 3.1, 3.6, and opens a whole marketing channel no competitor has.
- **Build cost:** ~2 days — static site generator reading the Evidence Graph (5.2) + anonymization pass + monthly cron. Defer to after 10 paying scans so the index has signal.

---

## 6. Economically sequenced roadmap — every dollar spent on build is already priced into an existing tier

Each phase funds the next. No capital outlay. Every build cost is an afternoon to a few days.

### Phase 1 — **Repackage, don't rebuild** (week 1, ~6 hours total)
- Rename scan sections internally to the six-module vocabulary above.
- Add `recovery_per_hour` sort to the 30/60/90 plan (§5.4 — 2 hours).
- Assemble the 1-page Legal Posture Audit from existing citations (§5.3 — 4 hours).
- **Outcome:** same product, named modules, clearer sales story. Ship in the next scan PDF.
- **Revenue unlock:** justifies the Tier 2 $79/mo price by giving it two named modules (Evidence Graph access preview + Legal Shield) instead of "monthly re-scan."

### Phase 2 — **Evidence Graph appender** (week 2, ~1 day)
- JSONL log of every scan's signal tuples keyed on business.
- Drift-delta helper returning `{signal: {severity_change, new_quotes}}`.
- Wire into Tier 2 monthly re-scan email (drift alert).
- **Outcome:** Tier 2 subscribers see their own evidence compound; retention argument writes itself.
- **Revenue unlock:** doubles LTV of Tier 2 — a subscriber who sees their own 60-day drift chart doesn't churn.

### Phase 3 — **Operator Co-pilot landing page + retainer SKU** (week 3, ~4 hours)
- One-page explainer on gojetpakt.com for the retainer posture.
- Calendly or email-based onboarding flow.
- **Outcome:** the $1,200/mo or $99+5% tier becomes a published SKU, not a conversation.
- **Revenue unlock:** one retainer at $1,200/mo = ~15 Tier 2 subscribers at $79. Tier 5 is the highest-leverage slot.

### Phase 4 — **Denver Severity Index public page** (month 2, ~2 days) — only after 10 paid scans
- Static page generated from Evidence Graph, anonymized, neighborhood-bucketed.
- Update monthly via cron.
- **Outcome:** SEO + social proof + referral flywheel. Cost-per-acquired-customer drops because the public index becomes the sales collateral.
- **Revenue unlock:** expected 2-3x inbound lift over 90 days based on [local-SEO benchmarks for published data pages](https://reputation.com/resources/articles/premium-google-my-business-features); not booked in the model until observed.

### Phase 5 — **Quarterly legal review partnership** (month 3, ~negotiation only)
- Identify one Denver hospitality-adjacent attorney willing to do 30-min review calls at $89 retail (likely $40-60 cost).
- Offer as Tier 3 add-on.
- **Outcome:** converts Legal Shield from "vendor expertise" to "actual lawyer signed off," which is the only claim [SOCi/Chatmeter](https://www.soci.ai/industries/restaurants/) can credibly make at enterprise.
- **Revenue unlock:** justifies raising Tier 3 to $199 or holding $179 while widening conversion from Tier 2.

**Total build time: ~4 working days across 3 months. Total cash outlay: $0.** Every hour is funded by the Tier 1 $49 scans already shipping.

---

## 7. What this does *not* do

Being disciplined about what's out of scope:

- **No attempt to compete on review-site breadth.** Birdeye (150 sites), Reputation (250), Chatmeter (85), TrustYou (200) all win this race. JetPakt wins on depth per site, not breadth across sites.
- **No auto-response feature — ever.** That's the moat. Adding it erases §3.5.
- **No dashboard app.** The PDF is the deliverable. A web dashboard is a Phase-5+ consideration only if operators explicitly request it; until then, the PDF-as-deliverable is the differentiator.
- **No attempt to serve enterprise chains.** SOCi and Chatmeter own that market at $16k-$62k/yr. JetPakt's Tier 6 Enterprise at $24k/yr is the ceiling, not the target — it exists so multi-location referrals have a landing pad, not as a GTM focus.
- **No expansion beyond hospitality.** The signal library, ROI elasticities, and peer benchmarks are hospitality-specific. General-purpose reputation tools ([NiceJob](https://get.nicejob.com/pricing), [Grade.us](https://www.grade.us/home/plans/)) lose on depth precisely because they spread thin. JetPakt stays narrow.

---

## 8. The elevator version

JetPakt is the only reputation tool in the category that ships an **evidence-cited severity score, a defensible ROI range, a defamation-safe response draft, and a platform-rule legal posture audit — as a consulting-grade PDF, with a human holding the send button, at a price point independents can expense.** Every competitor either charges 10x more (SOCi, Chatmeter), auto-sends into defamation risk (Podium, Birdeye, indie SaaS), punishes per-location (Reputation, Birdeye, ReviewTrackers), or sells a generic dashboard with no economic model (all of them).

The restructure in §5 turns the six already-shipped strengths into six named, sellable modules. The roadmap in §6 funds itself out of existing Tier 1 revenue, in four working days spread across three months, with zero capital outlay.

---

*Matrix data: [`wide/research_results_mo3yo46y.csv`](../../wide/research_results_mo3yo46y.csv) (12 competitors × 17 fields, verified April 2026). Pricing and features cross-checked against vendor sites, G2, Capterra, and third-party analyses cited inline.*
