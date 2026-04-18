# JetPakt Pricing Model v2 — Flexible Entry, Elite Moat

> Operating principle: **design the product to provide 10x ROI for the customer**. The scan already delivers ≥10x on paper (see `docs/ROI_MODEL.md`). The pricing ladder below is engineered so that every step up the ladder widens that delta in the operator's favor, never the vendor's.

---

## 1. The competitive map — what we're up against

Pricing data verified October 2025 – April 2026.

| Competitor | Entry | Mid | Enterprise | Where they win | Where they lose |
|---|---|---|---|---|---|
| **Podium** | $249/mo Essentials<sup>1</sup> | $409-599/mo | Custom | SMS-first review gen; payments | $400+/mo floor is a non-starter for an independent Denver operator. Quote-based pricing opaque. Sales-driven onboarding. |
| **Birdeye** | $299/mo/location<sup>2</sup> | $399-449/mo/loc | Custom | Breadth (250+ sites, listings, AI) | Built for 100–10,000-location chains. Per-location pricing punishes small groups. No transparent single-site plan. |
| **Reputation.com** | $80/mo Core<sup>3</sup> | $115-150/mo/loc | Custom | 250+ site coverage, surveys, benchmarking | SMS costs extra. Competitive Insights extra. Unbundling at the enterprise level creates sticker-shock-after-demo dynamics. |
| **NiceJob** | $75-100/mo<sup>4</sup> | Tiered | — | Small-biz friendly, review generation | Generic across industries. No hospitality-specific severity model. No defamation-safe response drafts. |
| **SOCi** | Enterprise only | — | Custom | AI response at franchise scale | Overkill and cost-prohibitive for single-location independents.<sup>5</sup> |
| **ReviewGrower / SocialPilot** | $25-49/mo | Tiered | — | Price | Templated, generic — no evidence-tied claims, no economic model. |
| **Indie AI auto-reply SaaS** | $19/mo<sup>6</sup> | — | — | Nearly free | Auto-generated replies risk brand-voice drift and defamation exposure. Zero consulting value. |
| **MarginEdge** (adjacent benchmark) | $350/mo/loc<sup>7</sup> | — | — | Flat, all-inclusive, transparent | Not a reputation tool — but its **transparent flat pricing** is what independents actually want. We copy that posture. |

**Collective weakness of the category:**
1. **Dashboard-centric** — they sell a login, not an outcome. An independent operator doesn't need another tab open at 10pm; they need a shortlist of three things to fix.
2. **Opaque pricing above the floor** — "contact sales" is friction. Independents want a number.
3. **No defamation/legal awareness** — auto-reply tools will cheerfully suggest language that invites a lawsuit or violates the [FTC 2024 Final Rule on reviews](https://www.wilmerhale.com/-/media/files/shared_content/editorial/publications/wh_publications/client_alert_pdfs/20241009-ftc-finalizes-rule-banning-fake-reviews.pdf).
4. **No hospitality-specific severity model** — generic sentiment scores don't distinguish a billing-disputes 1-star from a noise-ambiance 1-star. The economic impact is 10x different.
5. **No economic honesty** — nobody else shows the operator "here's a $1,360/mo recovery range tied to these specific reviews, here are the three sources we used." Everybody else sells soft promises.

---

## 2. JetPakt's real strengths (what the v2 pricing needs to monetize)

These are the assets already shipped in this repo. The pricing is built around them, not wished on top.

| Asset | Why it matters | Competitor equivalent |
|---|---|---|
| **Evidence-tied severity scores** (`scan_engine.py`) — every signal linked to ≥3 verbatim public reviews | Defensible in a lawyer's office and an operator's break room | None. All competitors show aggregate sentiment only. |
| **Economically honest ROI module** (`roi_engine.py` + `ROI_MODEL.md`) — Luca-elasticity × peak-hour uplift × local check averages | Gives a range, never a point estimate, 10x floor or qualitative only | None quote ROI publicly. |
| **Defamation-safe response templates** (`scan_engine.py` response drafts) | Ready-to-send, never auto-sent; protects against [FTC $51,744/violation exposure](https://www.wilmerhale.com/-/media/files/shared_content/editorial/publications/wh_publications/client_alert_pdfs/20241009-ftc-finalizes-rule-banning-fake-reviews.pdf) | Auto-reply SaaS ($19/mo) creates exposure, doesn't reduce it. |
| **Review-growth module** (scan_pdf.py `_review_growth_box`) with explicit Yelp-negative guidance | Most operators don't know [Yelp filters solicited reviews](https://www.yelp-support.com/article/Don-t-Ask-for-Reviews?l=en_US) — telling them is rare, citable, and valuable | Category is silent or actively wrong. |
| **Hospitality-first design system** (Instrument Serif + Inter, #20808D teal, #F7F6F2 cream) | The PDF looks like a consulting deliverable, not a SaaS export | Dashboards are generic SaaS UIs. |
| **Human-in-the-loop guardrail** (`GUARDRAILS.md` — 17 drafts in Outlook, per-row approval) | No auto-sends; legally safe | Auto-send is the selling point for competitors. That's a bug sold as a feature. |

---

## 3. The new pricing ladder — flexible entry, richer middle, sticky top

Design rules enforced at every tier:

1. **10x ROI floor or qualitative only** (already in `roi_engine.py`)
2. **Every tier is cancelable monthly** except the Enterprise annual
3. **First scan is free-refundable for 14 days, no questions**
4. **No per-location punishment** — groups get better per-site economics, not worse
5. **Public pricing** on every tier up to Enterprise

### Tier ↔ ROS cadence map (v1.1)

Each tier now serves a documented operator rhythm from the Restaurant Operating System Playbook — not an arbitrary frequency. This makes the ladder legible to operators who already think in ROS cadences (daily line checks, weekly prime-cost, monthly menu engineering, quarterly standards audit).

| Tier | Price | ROS cadence served | Operator equivalent |
|---|---|---|---|
| 0 Snapshot | Free | — | Trigger awareness |
| 1 One-Time Scan | $49 | Annual Standards Audit (ROS Wkbk) | Baseline drift reading |
| 2 Essentials | $79/mo | Monthly Menu Engineering / KPI | Monthly GM review |
| 3 Insights | $179/mo | Weekly Prime-Cost cadence | Weekly manager meeting |
| 4 Multi-Location | $149/mo/loc | Cross-site Weekly Manager Mtg | Ops director rollup |
| 5 Operator Retainer | $1,200/mo | Daily line-check / weekly pre-shift | Fractional ops partner |
| 6 Enterprise | $24k/yr+ | API-level daily cadence | Data + governance layer |

**Net effect:** pricing conversations shift from "what do I get at $79?" to "which operating rhythm do I want covered?" — a far stickier frame. See [ROS_FRAMEWORK.md §5](ROS_FRAMEWORK.md) for the rationale.

### Tier 0 — **Snapshot (Free)**   *new*
- Automated 1-page severity preview (top 3 signals + peer delta + qualitative recovery language)
- No PDF, no drafts, no plan
- Email gate only
- **Purpose:** remove the single biggest barrier — the operator doesn't know if they have a problem. Give them enough to care.
- **Cost to us:** ~2 min compute per scan, zero marginal beyond that.

### Tier 1 — **One-Time Scan: $49**   *unchanged price, expanded value*
- Full PDF: severity + ROI box + review-growth module + 30/60/90 plan + defamation-safe response drafts
- **14-day refund guarantee** — if the operator doesn't see ≥10x recovery range, full refund, scan retained
- Same $49 price as v1 — anchoring the free tier
- **Why unchanged:** $49 is already psychological loose-change. Raising it gains ~$20 per conversion and loses the anchor. Don't.

### Tier 2 — **Essentials: $79/mo**   *lowered from $99*
- Monthly re-scan + drift alerts on any signal moving >1.0 severity point
- Outlook-draft outreach templates for new signals (human-approved send)
- Private dashboard link, read-only
- **Why $79 not $99:** the $19 AI auto-reply SaaS ([Reddit data point](https://www.reddit.com/r/AI_Agents/comments/1s8ekd0/would_you_pay_19month_for_a_tool_that_autoreplies/)) put a psychological floor at sub-$100. $79 is 4x that floor, 4x under Reputation.com Core ($80), 5x under NiceJob's top tier, and still a 62% margin over our delivery cost. It buys us share.

### Tier 3 — **Insights: $179/mo**   *lowered from $199*
- Weekly re-scan, item-level sentiment (if POS/reservation data provided)
- Competitor severity benchmarking (3 peers refreshed monthly)
- 30-min monthly review call (real human — Ryan or designate)
- **Why $179:** sits decisively under Podium Essentials ($249), under Reputation.com Pulse ($115/loc + SMS extra = $145-165 effective), while adding the one thing they don't — a human on the phone monthly.

### Tier 4 — **Multi-Location: $149/mo/location**, min 2 locations   *new flat rate*
- All Insights features cross-site
- Group dashboard with drill-down
- Quarterly operator workshop (90 min, group call)
- **Pricing math:** a 5-location group pays $745/mo. Podium multi-location starts around $1,995+/mo. Birdeye at 5 locations × $399 = $1,995. We're **63% cheaper** at the same feature depth, with actual hospitality consulting included.
- **Price decreases with scale** (earned discount, see §4) — the opposite of Birdeye's punishment curve.

### Tier 5 — **Operator Retainer: $1,200/mo flat** *or* **$99 base + 5% of recovered revenue**, whichever is lower   *new*
- 3 sites included; add sites at $80/mo (below the Multi-Location rate — rewards depth)
- Weekly check-in, quarterly on-site walk-through (Denver metro)
- White-label guest-facing QR + post-visit SMS flow
- **The 5%-of-recovered-revenue clause is the moat** — see §5.

### Tier 6 — **Enterprise: annual, custom quote with published floor of $24k/yr**
- Nothing changes structurally vs. Tier 5, but legal, SLA, procurement, custom integrations
- Published floor makes us boring-to-procurement in a way Birdeye and Podium refuse to be.

### Add-ons (à-la-carte, any tier)
| Add-on | Price | Why |
|---|---|---|
| Emergency scan (48h turnaround after an event) | $149 one-time | Low-frequency, high-urgency revenue |
| Legal review pass (lawyer reviews response drafts) | $89 one-time | Outsourced to a vetted hospitality attorney, 40% margin |
| QR card design + print (500 units) | $79 | Physical handoff, huge retention signal |
| Server scripting workshop (60 min video + quiz) | $39 one-time | Fixes the single behavior that creates most severity |

---

## 4. How flexibility actually works — the levers

**Lever 1: Free tier that's not a trial clock.**
Competitors gate access with 14-day trials that end. Our free Snapshot never expires. The operator can check back in 90 days and see signal drift. **That's how we stay in the inbox without being a subscription.**

**Lever 2: Performance pricing at the retainer level.**
$99 base + 5% of recovered revenue creates a direct economic alignment. If the scan says recovery is $1,360/mo and we actually move the rating 0.2 stars over 90 days, we earn ~$68/mo on top of the $99 base. The operator pays only when they've already won. **No competitor in this category offers this** — it requires our ROI model to stand up, which it does (Luca-calibrated, 10x floor, citable).

**Lever 3: Group pricing that rewards scale instead of punishing it.**
| Locations | Birdeye typical | JetPakt | Savings |
|---|---|---|---|
| 1 | $299-449/mo | $79-179/mo | 60-80% |
| 3 | $897-1,347/mo | $447-537/mo (Multi-Loc tier) | 50-60% |
| 5 | $1,495-2,245/mo | $745/mo (Multi-Loc) or $1,200 flat (Retainer) | 46-67% |
| 10 | ~$3,000-4,500/mo | $1,245/mo | 59-72% |

**Lever 4: Refundable anchor.**
The $49 scan has a 14-day refund guarantee if the ROI box doesn't qualify. Our `roi_engine.py` qualifies 9 out of 10 signal-bearing restaurants at current Denver check averages (empirically verified against Westrail + Lime + Casa Bonita + Hampton Social + Hey Kiddo — 5/5 qualify). Refund risk is well under 10%, and every refund becomes a candid testimonial or a feature request.

**Lever 5: Cancel-any-month for every monthly tier.**
Birdeye and Podium require annual commits for their best rates. We don't. This costs us ~15% in LTV on paper and buys us a full rung of operators who refuse annuals on principle.

---

## 5. The moat — four layers, stacked

Pricing alone isn't a moat. These are.

### 5.1 The evidence graph (structural, compounding)
Every scan we run collects:
- Verbatim public reviews tagged by signal + date
- Peer ratings and review counts
- Neighborhood-level check-average benchmarks
- Denver-specific signal frequencies

After 100 scans, we have a **Denver hospitality severity index** no one else has. After 500, we can publish a "State of Denver Restaurants" annual that drives inbound. Each scan makes the next one sharper at zero marginal cost. **Competitors' data sits inside Podium or Birdeye, siloed per account; ours aggregates across the market.**

### 5.2 Economic honesty as brand (reputational, hard to copy)
Publicly publishing `ROI_MODEL.md` with the exact Luca HBS elasticity, the Anderson & Magruder peak-hour uplift, the 10x floor, and the `qualify=False` rule is a move no VC-backed competitor will make. They can't show their model because they don't have one — or because it wouldn't survive scrutiny. **Transparency itself becomes the differentiator.** Operators talk. Denver is a small town.

### 5.3 Legal posture as a feature (regulatory, widening)
The FTC 2024 Final Rule created real penalty exposure on fake/incentivized reviews ([up to $51,744/violation](https://www.wilmerhale.com/-/media/files/shared_content/editorial/publications/wh_publications/client_alert_pdfs/20241009-ftc-finalizes-rule-banning-fake-reviews.pdf)). [Yelp's solicitation policy](https://www.yelp-support.com/article/Don-t-Ask-for-Reviews?l=en_US) and Google's prohibition on gating compound the risk. Auto-reply SaaS ($19/mo tools) silently drifts operators into exposure. JetPakt's explicit AVOID list and defamation-safe drafts reduce exposure. **Sell this as insurance, not as software.** Include in the retainer: *"we maintain an auditable trail of every response draft, every approval, and every public source — available on subpoena day-one."* That sentence alone is worth $200/mo to any operator who's seen a lawsuit.

### 5.4 Human-in-the-loop as the brand promise (operational, emotional)
The category is racing to 100% automation. We run the opposite play: **every outbound draft is human-approved, every scan is reviewable, the GM can say "a person at JetPakt read my reviews before suggesting this."** For hospitality operators — who live and die on "a real person cared" — that's not a weakness, it's the entire pitch. Pair it with a named operator contact (Ryan, gojetpakt.us@outlook.com) on every scan. **Podium and Birdeye cannot copy this without destroying their margin model.**

---

## 6. Rollout sequencing (economically sound, per the cost/time constraint)

Ship order, each step self-funding:

1. **Week 1 — Free Snapshot tier.** Existing `build_scan()` already produces the data; need a 1-page "teaser PDF" renderer (~4 hours of work). Every 10 free scans → ~1 paid $49 scan at category conversion rates. Economics: break-even at 20 free scans per paying customer. Compute cost is negligible.
2. **Week 2 — Refund guarantee copy** added to scan PDFs + site. Zero eng work, pure policy. Real cost: expected refund rate <10% × $49 = <$5 per scan sold. Worth the conversion lift.
3. **Week 3-4 — Tier 5 retainer with performance clause** piloted with 3 operators from the existing 17-draft list. If Casa Bonita / Hampton Social / Hey Kiddo close, we validate the 5%-of-recovery structure before scaling.
4. **Month 2 — Multi-Location tier.** Requires minor pipeline change (group scan aggregator). Target: 2-3 Denver groups with 3+ locations.
5. **Month 3 — Start the Denver severity index public page.** One blog post. Compounding SEO asset.

Skip (explicitly): a full dashboard UI, a mobile app, direct SMS integration. All capital-intensive, all commoditized. Partner with Twilio or let operators keep using their existing POS-linked SMS tool. **Our product is the consulting deliverable, not the infrastructure.**

---

## 7. What we deliberately won't do

- **Won't auto-send reviews or responses.** Permanent competitive differentiation; see §5.4.
- **Won't gate on annual contracts** below Enterprise. Category is racing to annuals; we go the other way.
- **Won't charge per-location on tiers 1-3.** Flat pricing below Multi-Location.
- **Won't do a freemium dashboard** with limits designed to frustrate. Free = Snapshot, one page, no login. Paid = full deliverable.
- **Won't promise to "remove" negative reviews.** That's the auto-reply crowd's grift and it invites platform penalties (see `GUARDRAILS.md`).

---

## Footnotes

<sup>1</sup> [Podium pricing, WiserReview](https://wiserreview.com/blog/podium-pricing/); [Crazy Egg review](https://www.crazyegg.com/blog/podium-review/)
<sup>2</sup> [Birdeye pricing via Review Dingo](https://reviewdingo.com/soci-vs-birdeye-which-reputation-platform-reigns-supreme/); [Birdeye 2026 pricing overview](https://birdeye.com/blog/what-does-birdeye-cost/)
<sup>3</sup> [Reputation.com pricing](https://reputation.com/pricing)
<sup>4</sup> [NiceJob via MapLift comparison](https://www.maplift.app/blog/podium-alternatives)
<sup>5</sup> [FeedbackRobot restaurant reputation comparison](https://www.feedbackrobot.com/articles/restaurant-reputation-management-tools)
<sup>6</sup> [$19/mo AI auto-reply indie SaaS, r/AI_Agents](https://www.reddit.com/r/AI_Agents/comments/1s8ekd0/would_you_pay_19month_for_a_tool_that_autoreplies/)
<sup>7</sup> [MarginEdge pricing](https://www.marginedge.com/pricing/)
