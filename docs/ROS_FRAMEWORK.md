# ROS × JetPakt — Framework Integration

**Version:** 1.0
**Owner:** Ryan B. · gojetpakt.us@outlook.com · Gojetpakt.com
**Status:** Foundation — guides product roadmap, signal taxonomy, and pricing ladder

---

## 1. What is the Restaurant Operating System?

The Restaurant Operating System (ROS) is a five-pillar operating model for full-service restaurants, compiled into five deliverables:

| File | Role |
|---|---|
| Textbook | Operating science — 5 pillars, 49 principles, 24 case studies, Monte-Carlo evidence |
| Operator Playbook | What-to-do — tools and cadence per pillar |
| Operating Principles | Why — 49 principles across 7 intellectual domains |
| Recipe Guide | Combinations — principle-guided "recipes" for real problems |
| Checklists & Trackers Workbook | Ready-to-use daily/weekly/monthly forms |

The framework's core claim: **restaurants fail from quiet, accumulated drift** — a portion creeps, a check-back disappears, a pre-shift is skipped. ROS treats operating a restaurant as an engineering problem with a human core. Every pillar has tools, cadence, and measurable drift signals.

### The five pillars

| # | Pillar | Domain | One-line |
|---|---|---|---|
| 01 | **Production** | Kitchen | Every plate built to spec, every shift |
| 02 | **Service** | Front of House | Hospitality engineered as a system |
| 03 | **Sales** | Menu + Demand | The menu as an engine, not a list |
| 04 | **Operations** | Infrastructure | The restaurant as a reliable machine |
| 05 | **Management** | Leadership | The weekly rhythm that compounds excellence |

### The 24 cases (drift scenarios)

Production: I01–I05 · Service: I06–I09 · Sales: I10–I13 · Operations: I14–I18 · Management: I19–I24.

Each case = **symptom cluster → root causes → principles → action plan → simulated weekly revenue lift** with 95% CIs. This is the vocabulary JetPakt now adopts.

---

## 2. Why integrate ROS into JetPakt?

JetPakt started as a **reputation-intelligence scanner**: public reviews → signals → severity → 30/60/90 plan. The product was already good at surfacing *what is broken*. The ROS framework gives us three things we didn't have:

1. **Structural vocabulary** — pillars let operators see a severity 7.0 on service_pacing and immediately know "this is a Service-pillar drift, specifically I06 (table turn times)." Operators manage by pillar; so should our scan.
2. **Principle-guided prescriptions** — every action plan can now cite *why it works* (Theory of Constraints, Six Sigma, Pareto, Game Theory) rather than reading like restaurant folklore.
3. **Quantified case benchmarks** — ROS ships simulated weekly-revenue-lift ranges per case. These become the credible upper bound on JetPakt's ROI recovery model and a defensible claim surface for sales.

### Strategic positioning shift

| Before ROS | After ROS |
|---|---|
| "Reputation intelligence for Denver independents" | "Drift detection across the five operating pillars — starting with the reputation surface and expanding operationally" |
| Flat 10-signal taxonomy | Pillar-organized taxonomy with case links and principle citations |
| Severity ratings + generic 30/60/90 | Severity ratings + pillar + case ID + principle basis + simulated lift range |
| Single moat: legal-aware Denver reviews | Layered moat: reviews → pillars → cases → principles → cadence |

**This is an expansion, not a pivot.** The reputation surface stays the customer acquisition wedge because reviews are the cheapest, most public drift signal. Pillars give us a roadmap to earn operational data access later (POS/KDS integrations = Operations and Management pillars).

---

## 3. Signal → Pillar → Case mapping

Every JetPakt signal maps to at least one ROS pillar and one case. This is the Rosetta stone between our product and the framework.

| JetPakt signal | Primary pillar | ROS case(s) | Key principles | Why this mapping |
|---|---|---|---|---|
| `service_pacing` | Service | I06 (table turns), I01 (expo bottleneck) | Theory of Constraints, Six Sigma, Drucker | Pacing complaints almost always trace to expo as the throughput ceiling or to uneven steps-of-service. ToC + Six Sigma give the fix (role split, variance reduction). |
| `service_fee_transparency` | Sales | I10 (check size), I12 (review response), I22 (P&L review) | Game Theory, Kahneman (loss aversion) | Junk-fee complaints compound when unaddressed publicly. Game theory frames vendor/guest payoffs; loss aversion explains why an undisclosed fee feels 2x worse than a listed one. |
| `food_quality` | Production | I02 (execution variance) | Scientific Management (Taylor), Six Sigma, Aristotelian Virtue | Consistency is the product of codified spec + habituated practice. Recipe Bible + calibrated line checks are the tools. |
| `food_safety` | Production | I05 (HACCP drift) | Reliability Engineering, Systems Thinking | Safety is a reliability problem; logs + redundancy + calibration prevent the single-point failure. |
| `cleanliness` | Service | I09 (ambience degrades) | Operational Excellence, Broken Windows | Standards audits + nightly sign-off prevent the "first broken window" effect. |
| `staffing` | Operations | I16 (turnover drives perpetual understaffing) | Herzberg (hygiene vs. motivators), Systems Thinking | High turnover is a systems symptom — comp, training, respect. FOH pacing complaints often point here. |
| `billing_disputes` | Management | I18 (cash handling controls), I22 (P&L review) | Principal-Agent, Verification | Billing errors are controls + transparency issues. POS audits + menu-to-POS reconciliation fix both. |
| `noise_ambiance` | Service | I09 | Environmental Psychology | Acoustic and lighting standards are infrastructure decisions dressed as hospitality. |
| `server_attitude` | Service | I07 (steps-of-service inconsistency) | Situational Leadership, Pre-Shift Lineups | Attitude drift = training + recognition drift. Daily pre-shift + mystery-diner rubric reset the standard. |
| `pricing_value` | Sales | I10 (check size), I11 (menu engineering) | Menu Engineering (Kasavana-Smith), Anchoring | Value perception is engineered through the menu, not discovered through the price tag. |

### Signals the framework says we're missing

These are ROS cases JetPakt's review-signal surface does **not** detect today. They are review-invisible but operationally critical. Call them out to prospects to position JetPakt Scan as the wedge — not the whole platform.

| Case | Pillar | Why review-invisible | Future JetPakt product? |
|---|---|---|---|
| I03 (food cost 3–5 pts above budget) | Production | Guests don't feel it until portions shrink | POS/inventory integration — Enterprise tier |
| I14 (prime cost > 62%) | Operations | Same as above — P&L surface | Operator Co-pilot — Monthly reporting |
| I15 (vendor reliability) | Operations | Internal supply-chain signal | Vendor Scorecard tool — Multi-location tier |
| I16 (turnover) | Operations | Partial visibility via server_attitude churn in reviews | HR/scheduling integration — Enterprise |
| I11 (menu engineering undone) | Sales | Partial visibility via pricing_value | Menu analytics add-on — Weekly Insights |

**Strategic note:** These gaps justify the pricing ladder's upper tiers (Multi-Location, Enterprise) because they require integrations reviews can't deliver.

---

## 4. Principle-guided action plans

Each entry in `PLAYBOOKS` in `scan_engine.py` can now cite principles. The pattern:

```
Signal: service_pacing
Pillar: Service (I06) + Production (I01)
Principles: Theory of Constraints, Six Sigma, Drucker
30-day action: Split expo into Caller + Plater — measurable: ticket-time SD < 4 min
Why it works: ToC says throughput = bottleneck throughput. Splitting expo role is the
            lowest-effort way to break the ceiling. Six Sigma flags that SD matters
            more than the mean, so we measure SD.
```

This is additive — existing action text stays, but we expose `pillar`, `case`, and `principles` fields in the signal metadata so PDFs and future UI can surface them.

---

## 5. Cadence alignment — Pricing tiers ↔ ROS cadence

ROS prescribes a strict cadence: **daily line checks, weekly prime-cost review, monthly menu engineering, quarterly standards audit.** Our pricing ladder should mirror this.

| JetPakt tier | ROS cadence served | Deliverable |
|---|---|---|
| One-Time Scan ($49) | One-shot baseline | Annual Standards Audit equivalent |
| Monthly Essentials ($99/mo) | Monthly Menu Engineering / KPI review | Sentiment + signal drift report |
| Weekly Insights ($199/mo) | Weekly Prime-Cost cadence | Trend deltas, priority re-ranking, alerts |
| Multi-Location ($399+/mo) | Cross-site Weekly Manager Meeting | Roll-up dashboard, peer benchmarks across units |
| Enterprise Integration (custom) | Daily line-check / API-level cadence | POS/KDS/HR data, SSO, governance |

**Consequence:** pricing is no longer arbitrary — each tier serves a documented operator rhythm from the ROS Playbook. This is a defensible sales story.

---

## 6. The Drift concept — JetPakt's new product frame

**Before:** "We scan your reviews."
**After:** "We detect operational drift via the most public surface — reviews — and map it to the five pillars so you know which part of your operation is eroding."

The word "drift" reframes what JetPakt measures. A 3.3-star average isn't a bad rating; it's accumulated evidence that one or more pillars are drifting. Drift is measurable, trend-able, and fixable — which is exactly what an operator wants to hear.

Practical consequences in the scan output:

1. **Executive severity** becomes "Composite Drift Score" (UX copy change; math unchanged).
2. **Top signals** labeled with pillar chip (e.g., "SERVICE · I06 · Table Turn Drift").
3. **Action Plan** grouped by pillar rather than flat 30/60/90 — cleaner on page 2.
4. **Recovery model** cites the ROS-case revenue lift range alongside JetPakt's recovery math as a second anchor.

---

## 7. Updates this integration triggers

### 7.1 Signal library (code)

`scan_engine.SIGNAL_LIBRARY` gains three optional fields per signal:
- `pillar`: one of `"Production" | "Service" | "Sales" | "Operations" | "Management"`
- `case_refs`: list of ROS case IDs (e.g., `["I06", "I01"]`)
- `principles`: short list of principle names

**Backward-compatible.** Existing readers (`scan_pdf.py`, tests) that don't read these fields continue to work unchanged.

### 7.2 COMPETITIVE_ANALYSIS §5 (6 proposed modules)

The six modules (Scan Core, Evidence Graph, Legal Shield, Plain-English Playbook, Operator Co-pilot, Peer Pulse) now have a **framework spine** running through them:

- **Scan Core** → detects pillar-tagged drift, not flat signals.
- **Evidence Graph** → links review quotes to pillars, cases, and principles — audit-ready.
- **Legal Shield** → remains Denver-specific (HB25-1090). No change.
- **Plain-English Playbook** → now called **Principle-Guided Playbook**; every action cites 1–2 principles from the 49.
- **Operator Co-pilot** → adopts the ROS Weekly Cadence Master Stock (Recipe Guide Course V) as its planning engine.
- **Peer Pulse + Denver Severity Index** → extends with a "Pillar Heatmap" showing which pillar is the top source of drift across the peer set.

### 7.3 PRICING_MODEL.md

Add a second column to the 7-tier ladder explaining which ROS cadence the tier serves (already drafted in §5 above).

### 7.4 Response drafts

No change to the templates themselves. But the `build_response_drafts` output now includes a `pillar` and `case_ref` tag alongside `primary_signal`, so ops can route drafts to the right pillar owner (Chef for Production, GM for Service/Management, etc.).

---

## 8. Non-goals (what NOT to do)

1. **Don't rebuild JetPakt around the framework.** The framework is a lens, not a replacement. Reviews remain the primary data input.
2. **Don't ship the full 24-case library in the Scan PDF.** One pillar reference + one case ID per top signal is sufficient. More is clutter.
3. **Don't cite principles that don't apply.** "Theory of Constraints" belongs on a pacing signal; it does not belong on a cleanliness signal. Keep the mapping in §3 as the source of truth.
4. **Don't abandon Denver-specificity.** HB25-1090 + local peer benchmarks remain the moat national competitors can't cross. ROS is universal; JetPakt is Denver-grounded.

---

## 9. What the operator sees — before/after scan page 2

### Before

> **Top Signal: Service Pacing** — severity 7.4 (Operations)
> Evidence: 4 reviews citing long waits, bottleneck at peak
> 30-day: Table-touch cadence, expo timer
> 60-day: Section-load analysis
> 90-day: POS pacing monthly review

### After

> **Top Signal: Service Pacing** — severity 7.4
> **Pillar:** SERVICE (I06 · Table Turn Drift) · also touches PRODUCTION (I01 · Expo Bottleneck)
> **Principles:** Theory of Constraints · Six Sigma · Drucker
> **Simulated recovery range (ROS):** $3,046/week (I06) to $2,022/week (I01), combinable.
> Evidence: 4 reviews citing long waits, bottleneck at peak
> 30-day (break the constraint): Split expo Caller/Plater during peak; table-touch cadence
> 60-day (reduce variance): Section-load analysis, capped at 5 tables per server
> 90-day (institutionalize): Monthly POS pacing review; ticket-time SD target < 4 min

Same length. Substantially more authority.

---

## 10. Roadmap in 3 waves

**Wave 1 (this integration, ~1 day):**
- SIGNAL_LIBRARY gets pillar/case/principles fields.
- PLAYBOOKS entries get an optional `principle` per action.
- COMPETITIVE_ANALYSIS §5 + PRICING_MODEL.md updated with framework spine.
- Scan PDF page 2 gets pillar chips (next scan build).

**Wave 2 (next 2 weeks):**
- Pillar Heatmap added to Scan Core output.
- Principle-Guided Playbook page in Scan PDF — one box per top signal citing the 1–2 principles.
- Recovery model cites ROS-case revenue range alongside our own math.

**Wave 3 (next quarter — requires integrations):**
- POS/KDS connectors unlock Production (I03 food cost, I14 prime cost) and Operations (I15 vendor) cases.
- HR integration unlocks I16 (turnover).
- Multi-Location tier delivers cross-unit Pillar Heatmaps — reflecting the ROS Weekly Manager Meeting cadence at a group level.

---

## Appendix A — ROS Pillar cheat-sheet for sales conversations

> "We don't just scan reviews — we map them to the five operating pillars every full-service restaurant runs on. When we show you a severity 7 on service pacing, we tell you exactly which pillar is drifting, which documented case it matches from the 24-case operator library, and which management principles fix it. That's why our plans land — they're not opinions, they're engineered."

## Appendix B — The 24 cases, one line each

| ID | Pillar | Title |
|---|---|---|
| I01 | Production | Saturday-night ticket times blow past 20 minutes |
| I02 | Production | Inconsistent dish execution across shifts and cooks |
| I03 | Production | Food cost 3–5 points above budget, no clear culprit |
| I04 | Production | Critical equipment fails mid-service, no backup |
| I05 | Production | HACCP logging inconsistent, drift risk |
| I06 | Service | Table turn times 15–20 min over target |
| I07 | Service | Server steps-of-service execution inconsistent |
| I08 | Service | Guest complaint escalates publicly, mishandled |
| I09 | Service | Restroom / dining room ambience degrading |
| I10 | Sales | Average check size trending below potential |
| I11 | Sales | Menu engineering not performed regularly |
| I12 | Sales | Online review response slow or absent |
| I13 | Sales | Seasonal specials launched without server training |
| I14 | Operations | Prime cost (food + labor) exceeds 62% |
| I15 | Operations | Vendor deliveries late, short, or quality issues |
| I16 | Operations | High turnover drives perpetual understaffing |
| I17 | Operations | POS failure during service, no backup |
| I18 | Operations | Cash handling / tip reporting has material gaps |
| I19 | Management | Management team lacks structured communication |
| I20 | Management | Performance management reactive, not proactive |
| I21 | Management | Standards auditing absent, SOP compliance drifts |
| I22 | Management | Weekly P&L reviewed too late, insufficient rigor |
| I23 | Management | New manager onboarding unstructured |
| I24 | Management | Large-party / event capacity planning fails |

**The JetPakt cases we address today (primary):** I06, I07, I08, I09, I12, I18, I22 — 7 of 24. That's a 29% surface-area coverage by the review-signal wedge. Integrations expand coverage into the remaining 17.
