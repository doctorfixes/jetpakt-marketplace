# AI Agency Automation Plan — 80134 Local Small Business

**Version:** 1.1 · **Owner:** Ryan (rmbrown119@gmail.com) · **Date:** 2026-07-11

You are the operator. This document specs the pivot to **JetPakt AI**, a single-operator AI Agency serving local trades and service businesses in and around Parker, CO (80134).

**Update from v1.0:** the original plan assumed a from-scratch build in a new repo. It turned out this repo already runs a second, live business — **JetPakt Pulse**, a restaurant-reputation product with a real Google Sheet and real Stripe products, wired to hourly cron automation (`jetpakt_cli/`). That business's config is untouched. JetPakt AI is now built as a **second profile** on the same CRM/outreach engine (`JETPAKT_PROFILE=agency`), in this repo, under the same JetPakt brand — not a separate codebase. See the root README's "What This Repo Runs" section.

---

## 1. Positioning

**Name:** JetPakt AI
**One-liner:** We give local service businesses a 24/7 AI receptionist, an instant booking page, and automated review follow-up — installed in a week, no app to learn.
**Who it's for:** Businesses in 80134 and adjacent zips that (a) miss inbound calls, (b) have no website or a broken one, (c) don't run any SMS/email follow-up. That is most of the target list.

**Why now, locally:** Parker/Douglas County is a high-income suburban corridor with heavy home-service demand (roofing after hail seasons, HVAC, plumbing, landscaping) and a dense personal-service layer (salons, spas, dry cleaners, dog groomers). Owners are one-truck / one-chair operators who lose revenue every missed call and can't afford a real receptionist.

**Target zip ring (drive-time proxy for in-person install visits):**
- Core: **80134, 80138** (Parker)
- Ring 1: **80104, 80108, 80109** (Castle Rock), **80130, 80126** (Highlands Ranch), **80124** (Lone Tree)
- Ring 2: **80016** (Aurora/Southlands), **80112** (Centennial)

---

## 2. Service Catalog

Four productized offerings. Every business gets #1 as the anchor; the rest attach as bundle upsells.

### S1 — AI Front Desk (anchor)
- 24/7 AI phone agent answers on a dedicated forwarded number
- Books appointments straight into the owner's Google Calendar
- Texts the caller a confirmation + directions link
- Escalates emergencies (leak, no-hot-water) to the owner's cell
- **Setup:** $997 one-time · **Monthly:** $397 (includes up to 500 answered minutes)

### S2 — One-Page Site + Google Business Profile
- Single static page templated per client (client owns the domain)
- Services, hours, service area, click-to-call, click-to-text, embedded booking
- Full GBP claim, category cleanup, photo upload, service list, Q&A seeding
- **Setup:** $497 one-time · **Monthly:** $97 (hosting + monthly GBP posts + edits)

### S3 — Review Autopilot
- Post-job SMS asks for a Google review with a deep link
- Owner-approved templates per service (salon vs. plumber wording differs)
- Weekly summary of new reviews + one-tap owner reply drafts
- **$197/mo, no setup fee** (as implemented — see `stripe_sync.AGENCY_PRODUCTS`). A bundle-attach discount can be layered on later as a Stripe coupon rather than a second canonical price.

### S4 — Lead Intake & Instant Quote
- Web form + inbound SMS keyword captures leads
- Rules engine returns instant quotes for standard jobs (drain clear, roof inspection, cut+color, shirts-per-pound) or "we'll call you in X minutes"
- Round-robin to owner's cell if no self-serve quote fits
- **Setup:** $297 one-time · **Monthly:** $147

### Recommended bundle
**"AI Front Desk Complete":** S1+S2+S3 for **$1,997 setup / $497 mo** (saves $141/mo vs. à la carte). This is the pitch on cold outreach.

---

## 3. Target Business List (first 100 accounts)

Prioritize businesses where (a) the phone is the primary sales channel and (b) missed calls = lost revenue same day.

| Vertical | Approx. count in 80134 ring | Pain fit | Priority |
|---|---|---|---|
| Plumbers | 40–60 | Emergency calls after hours; huge missed-call cost | **A** |
| Roofers | 60+ (hail belt) | Storm-driven call spikes; quote follow-up terrible | **A** |
| HVAC | 40+ | Same-day service, phone-only booking | **A** |
| Electricians | 30+ | Small shops, no receptionist | A |
| Salons/barbers | 80+ | Cancellations, no-shows, review-driven | **A** |
| Dry cleaners | 8–12 | Low ticket but sticky; SMS pickup reminders | B |
| Dog groomers | 20+ | Booking-heavy, review-sensitive | A |
| Landscape/lawn | 60+ | Seasonal spikes, quote-heavy | B |
| Mobile mechanics / auto detail | 20+ | Quote-and-book, texts convert | B |
| Med-spa / wellness | 30+ | High ticket, review-sensitive | A |

Sourcing (all free): Google Maps scrape via Places API (free tier: 200 requests/day is enough for weeks), Douglas County Chamber directory, Nextdoor business listings, Yelp local, GBP "no website" filter (Places API `website` field null).

---

## 4. Tech Stack

**Repo:** this repo (`jetpakt-marketplace`), same FastAPI backend the restaurant business already runs on — not a new repo. The table below reflects what's actually built vs. still to do.

| Layer | Choice | Status |
|---|---|---|
| Marketing site | Static HTML on the existing FastAPI static mount (`site/index.html`) → Netlify | **Built** — see `site/index.html` |
| Backend API | FastAPI (`main.py`, `api/routes/`) | **Built** — `/api/services`, `/api/webhooks/{stripe,vapi,twilio}` |
| CRM / outreach engine | `jetpakt_cli/` retargeted via `JETPAKT_PROFILE=agency` (see §5) | **Built** (mechanism) — Sheet/Stripe IDs still placeholders, human step required |
| Payments (catalog + webhook) | `stripe_sync.AGENCY_PRODUCTS` (canonical catalog) + `billing/stripe_client.py` (webhook verify/normalize) → feeds `jetpakt_cli.clients.build_onboarding_plan` | **Built** — no live Stripe products yet, see §8 |
| AI voice | **Vapi** (primary) with Retell fallback | **Not started** — needs a real Vapi account; webhook receiver exists (`/api/webhooks/vapi`) and is ready to log call events once wired |
| SMS | Twilio (needs A2P 10DLC registration — start now, takes 2–3 weeks) | **Not started** — webhook receiver exists (`/api/webhooks/twilio`) |
| Booking | Google Calendar direct via API, or Cal.com if a client wants a public booking page | **Not started** |
| Website generation (per-client) | Templated static page, one variant per vertical | **Not started** — the marketing site exists, per-client site templating doesn't yet |
| Reviews | GBP deep link via SMS; GBP API for reads only (write access is restricted) | **Not started** — Google won't let 3rd parties post reviews on a customer's behalf, so SMS-with-link is the only compliant path |
| Client portal | Deferred | **Not started** — not needed until first paying accounts exist |
| Observability | `output/{onboarding,calls,sms}/*.json` artifacts on disk for now | **Built** (minimal) — fine through the first ~20 accounts, revisit later |

**Hard "do not build" list (buy or skip, don't roll your own):** voice model, SMS carrier, calendar UI, review posting.

---

## 5. Free CRM: Retargeted `jetpakt_cli` Engine (not a new build)

The original v1.0 of this doc specced a brand-new six-tab Sheets + Apps Script CRM. That's now unnecessary — this repo already runs a working Sheets CRM + cold-outreach engine for the restaurant business (`jetpakt_cli/`), and it's vertical-agnostic under the hood (smoke gates, Sheet sync, Outlook drafting, inbox-scan classification, Stripe-triggered onboarding — none of that logic is restaurant-specific). JetPakt AI uses the same engine as a **second profile**, `JETPAKT_PROFILE=agency`, so there's one codebase and one CLI to maintain across both businesses.

### What's shared vs. separate

| | Restaurant (Pulse) | AI Agency |
|---|---|---|
| Mechanism (`cli.py`, `smoke.py`, `sync.py`, `outlook.py`, `inbox.py`, `clients.py`) | same code | same code |
| Google Sheet | live, real ID (untouched) | separate Sheet — **you create this**, see setup below |
| Stripe products | live, real product IDs (untouched) | separate products — **you create these**, see §8 |
| Welcome-email copy, Sheet-tab gids, product tiers | `config.py` `"restaurant"` profile | `config.py` `"agency"` profile |

### Sheet tabs to create (mirrors the restaurant Sheet's structure)

Create a new Google Sheet ("JetPakt AI CRM") with four tabs matching the schema `jetpakt_cli` already expects — same columns as the restaurant Sheet, since the mechanism is shared:

**`Prospects`** (26 cols, A–Z) — every business you're targeting, sourced or inbound. Full schema: `prospect_id, business_name, category, neighborhood, city, state, rating, review_count, peer_gap, rating_12mo_delta, priority_tier, dominant_pillar, ros_case_id, legal_flag_severity, google_url, yelp_url, website, owner_name, owner_email, source, stage, stage_entered_at, next_action_due, notes, created_at, updated_at`. For the agency, `category` holds the vertical (plumber/salon/roofer/...); `dominant_pillar`/`ros_case_id` are unused restaurant-ops columns — leave blank or repurpose for "which service is the pitch" later if useful.

**`Outreach Log`** (16 cols, A–P): `log_id, prospect_id, direction, channel, touch_type, template_version, subject, body_excerpt, draft_file, pillar, case_id, sent_at, reply_received_at, reply_sentiment, result, created_at`.

**`Suppression`** (6 cols, A–F): `email_or_domain, type, reason, prospect_id, suppressed_at, source`.

**`Clients`** (18 cols, A–R): `client_id, prospect_id, business_name, contact_email, stripe_customer_id, stripe_subscription_id, tier, cadence, mrr_usd, status, onboarded_at, next_deliverable_due, last_memo_sent_at, last_memo_file, cancellation_reason, notes, created_at, updated_at`.

After creating the Sheet and tabs, get each tab's numeric `gid` (Sheets URL when that tab is active, e.g. `...#gid=123456789`) and fill in `jetpakt_cli/config.py`'s `"agency"` profile: `sheet_id` (or set `JETPAKT_AGENCY_SHEET_ID` env var) and the four `worksheet_ids` entries, currently `None` placeholders.

### Service-delivery data (calls, bookings, reviews sent) — separate from the CRM

The CRM tabs above track the *sales pipeline* (lead → outreach → client). Day-to-day service delivery — AI phone calls, bookings, review sends — is a different concern, handled by the FastAPI webhook receivers (`/api/webhooks/vapi`, `/api/webhooks/twilio`), which currently write JSON artifacts under `output/{calls,sms}/`. Once account volume justifies it, add three more tabs (`Calls`, `Bookings`, `Reviews Sent`) to the same Sheet and have those webhook handlers emit sync plans the same way `jetpakt_cli.sync` does for outreach — not a new system, an extension of this one.

### Why not Airtable / HubSpot?
- **Airtable free** caps at 1,000 records/base. First outreach batch alone will fill that.
- **HubSpot free** has deal pipelines, but its API rate limits and rigid object model fight the "one row is one lead, edit inline in a VA-friendly grid" workflow. Fine to graduate to it at ~$5k MRR.
- Reusing `jetpakt_cli` avoids the bigger reason to say no to either: it's already built, tested (`tests/test_jetpakt_cli_profiles.py`), and wired to Stripe onboarding.

---

## 6. Sales & Delivery Process

### 6.1 Outreach (weeks 1–ongoing)
1. **Sourcing:** run a Places API scan of the zip ring for each vertical, filter for `website is null OR website contains 'facebook.com'`, dedupe against the `Prospects` tab. Target: 500 new rows/week.
2. **First touch:** 15-second personalized voicemail + follow-up SMS ("Saw you don't have a booking page — mind if I send a 60-sec Loom of what I built for a Parker plumber?"). Human-recorded voicemail per vertical, not AI — feels wrong and hurts trust on trades.
3. **Follow-up cadence:** SMS day 3, email day 7, drop-in visit day 14 for A-priority verticals in the core zip.
4. **Close artifact:** shared Google Doc proposal (never a PDF — you want them to be able to comment) linking a Loom of a live demo installed on `demo-{vertical}.gojetpakt.com`.

### 6.2 Discovery call (30 min)
- What's your current phone situation? (Answer service? Voicemail? Personal cell?)
- How many calls/day roughly? What % do you miss?
- Where do bookings live today? (Paper book, Google Cal, Square, Vagaro?)
- What's your Google review count and star rating?
- Who owns the current website (if any) and the GBP login?

Output: filled-in `Clients` row draft + a Loom recap sent within 2 hours.

### 6.3 Install week (5 business days)
- **Day 1:** Contract signed via Stripe checkout ($setup + first month's $mo). GBP ownership transferred or manager access granted. Domain access confirmed.
- **Day 2:** Vapi agent configured — voice, script, escalation number, calendar OAuth. Twilio number provisioned and forwarded to.
- **Day 3:** One-page site deployed to `{business}.com` or a `gojetpakt.com/{slug}` fallback. GBP updated with new website + hours.
- **Day 4:** Review autopilot template approved with owner. Test-fire an SMS to owner's cell.
- **Day 5:** Live walkthrough call with owner (Zoom or in-person for core-zip A accounts). Flip forwarding on. Owner keeps direct number for regulars.

### 6.4 Retention (ongoing)
- Weekly automated email: calls answered, bookings created, reviews received, dollars-of-work-booked estimate.
- Monthly 15-min "tune-up" call for first 90 days, then quarterly.
- Any month with call volume drop >30% or a 1-star review → same-day owner call.

---

## 7. Pricing & Unit Economics (rough)

| Line item | Per account / mo |
|---|---|
| Vapi minutes (500 incl., avg 300 used) | ~$18 |
| Twilio number + SMS (~200 msg) | ~$3 |
| Vercel + Cal.com hosting | ~$1 (amortized across accounts) |
| Stripe fees on $497 | ~$14 |
| **COGS** | **~$36** |
| **Price** | **$497** |
| **Gross margin** | **~93%** |

Setup fee ($1,997 bundle) covers your install labor (~4 hours) plus first-month risk buffer. At 50 accounts you're at **~$25k MRR / ~$23k gross profit/mo**, single-operator sustainable with one part-time VA on outreach.

Break-even math: one account pays for Vapi + Twilio for the next ~13 accounts. You can safely offer a **30-day money-back guarantee** on the anchor bundle — it removes the biggest cold-outreach objection and the actual refund risk is <5%.

---

## 8. Milestone Plan

### Days 1–7: Foundation
- [x] FastAPI backend: `/api/services` catalog, `/api/webhooks/{stripe,vapi,twilio}` receivers
- [x] `stripe_sync.AGENCY_PRODUCTS` canonical catalog (setup + monthly pairs, 5 services)
- [x] `billing/stripe_client.py` — Stripe webhook verify/normalize (DEV_MODE without live keys)
- [x] `jetpakt_cli` agency profile (`JETPAKT_PROFILE=agency`) — mechanism ready, Sheet/Stripe IDs are placeholders
- [x] Marketing site (`site/index.html`) — service catalog, pricing, CTA
- [ ] Create the AI Agency Google Sheet + 4 tabs (see §5), paste `sheet_id`/`worksheet_ids` into `config.py`
- [ ] Stripe Dashboard: create the 9 agency products/prices from `stripe_sync.AGENCY_PRODUCTS` (lookup_keys already defined), paste resulting product IDs into `config.py`'s `STRIPE_PRODUCT_TIER`
- [ ] Set `STRIPE_WEBHOOK_SECRET` + point a Stripe webhook endpoint at `/api/webhooks/stripe`
- [ ] Vapi account, one demo agent for a fake plumber, point its webhook at `/api/webhooks/vapi`
- [ ] Twilio account, kick off A2P 10DLC registration (blocks for 2–3 weeks — start now), point SMS status callback at `/api/webhooks/twilio`
- [ ] Deploy this backend somewhere with a stable public URL (Render/Fly/etc.) so the webhook URLs above resolve

### Days 8–21: Demo assets and 1st design partner
- [ ] Build 3 vertical variants of the one-page site template (plumber, salon, roofer)
- [ ] Record 3 vertical-specific Loom demos on the demo numbers
- [ ] Source 200 leads into the `Prospects` tab from the core zip (Places API scan)
- [ ] Sign one **free-pilot design partner** (no setup fee, first month free in exchange for a video testimonial). Ideal: a plumber or salon owner you already know.
- [ ] Install the pilot end-to-end. Fix everything that breaks.

### Days 22–45: First 5 paying accounts
- [ ] Run the outreach cadence at 500 leads/week
- [ ] Target: 5 paid installs in the core zip. All A-vertical.
- [ ] After install #3, record a case-study Loom with numbers (calls answered, bookings created)

### Days 46–90: Scale to 20
- [ ] Hire one part-time VA ($8–12/hr) for lead sourcing + first-touch SMS
- [ ] Ring 1 zips added to outreach
- [ ] Add Review Autopilot as default upsell after day-30 of any account
- [ ] Client portal (magic-link) shipped so owners self-serve transcripts/reports

### Days 91–180: 50 accounts, hire delivery help
- [ ] Second person on install day (contractor rate)
- [ ] Consider a "Reseller" tier for a Parker web designer to white-label the stack

---

## 9. Legal / Compliance Landmines (don't skip)

- **TCPA (SMS):** every outbound SMS to a customer of a client requires prior express consent. The pattern is: the AI agent tells the caller *"Is it OK if we text you a confirmation?"* — that verbal opt-in is your consent record. Log it on the `calls` row.
- **A2P 10DLC:** required by US carriers for any business SMS. Register the agency as the brand, register each client as a campaign. 2–3 week lead time. Start on day 1.
- **Colorado telecom:** two-party consent state for call recording. The Vapi agent must open with *"Calls are recorded for quality — is that OK?"* or you don't record. Non-negotiable.
- **GBP terms:** you can request reviews, you cannot filter, gate, or offer incentives for them. Review Autopilot templates must not say "if you had a good experience" (that's review gating and gets accounts suspended).
- **Client data:** call transcripts contain PII. Store them in a Vercel Blob / S3 bucket with a 90-day TTL by default, and give owners a self-serve "delete transcript" button in the client portal.
- **Website ownership:** the client owns their domain. Your Vercel account hosts, but the DNS and registrar login stay with them. Otherwise you have leverage they'll resent.

---

## 10. What Happened to the Old Code

This repo carried three prior identities before this pivot: a restaurant-ops alerting product (`docs/PRODUCT.md`'s original text), a bookkeeping marketplace (the old README/site), and — still live today — the JetPakt Pulse restaurant-reputation business (`jetpakt_cli/`). Here's what happened to each as part of this pivot:

- **Bookkeeping marketplace** (`marketplace/`, `verification/`, `api/routes/marketplace.py`, `tests/test_marketplace.py`, `stripe/escrow.py`) — **deleted**. It wasn't serving either the restaurant business or the new agency; pure dead weight from an earlier, unrelated pivot. The old `stripe/escrow.py` also had a real bug (the local `stripe/` folder shadowed the pip `stripe` package on import) that's moot now that it's gone.
- **`stripe/escrow.py`'s DEV_MODE pattern** — kept the *idea*, not the code (escrow hold/release/cancel doesn't apply to subscription billing). Rebuilt as `billing/stripe_client.py`, focused on webhook verification/normalization.
- **`main.py` FastAPI skeleton, `netlify.toml` deploy pattern** — kept and repointed at the new routes.
- **`jetpakt_cli/`, `stripe_sync.py`, the restaurant docs** (`ONBOARDING_PLAYBOOK.md`, `OUTREACH_TEMPLATES.md`, `GUARDRAILS.md`, `PULSE.md`, `ROS_FRAMEWORK.md`, `REPOSITION_V3_SPEC.md`, `COMPETITIVE_ANALYSIS.md`, `PRICING_MODEL.md`, `ROI_MODEL.md`, `BILLING.md`, `EMAIL_SETUP.md`, `OUTREACH_FREE_PILOT.md`) — **untouched**, still describe the live restaurant business. Nothing here was archived or deleted.
- **`docs/PRODUCT.md`** — kept its original restaurant-ops content, with the AI Agency description added below it under a clear header rather than overwriting.

Net effect: one repo, two businesses, shared mechanism where it made sense (CRM/outreach engine, Stripe sync pattern, FastAPI app) and separate data everywhere it mattered (Sheets, Stripe products, welcome copy).

---

## 11. Open Questions — Defaults Applied

Ryan doesn't have a firm answer on the legal-entity or design-partner questions yet. Rather than block on them, each gets a default below so the plan stays actionable; revisit whenever there's a real answer.

1. ~~**Brand name**~~ — **Decided: JetPakt AI.**
2. ~~**Domain**~~ — **Decided: gojetpakt.com** (reused, not a new purchase).
3. **Legal entity — default: invoice through the existing LLC, revisit at scale.** Lower friction, no new filing/EIN/bank account needed to start. Two things to do regardless of which entity: (a) get an E&O / cyber-liability rider added to whatever policy already covers JetPakt Pulse — this business touches call transcripts (PII) and answers a client's phone line, a different risk profile than a Sheets-based reporting product; (b) revisit a separate LLC if the agency clears roughly $10–15k MRR or if a specific liability scenario worries you (e.g., a missed emergency call). This isn't legal advice — loop in an accountant/lawyer before the first real contract goes out, but it shouldn't hold up building or piloting.
4. **Cell number for owner escalations — default: your own cell during the pilot.** Zero setup cost, and you want to hear the actual escalation calls while you're still tuning the AI agent's script. Move to a shared on-call number (Google Voice or a second Twilio line forwarded to you) once you're past ~10 accounts or want a night off.
5. **Free-pilot design partner — default: no pre-identified partner required.** Fold "find one" into the Days 8–21 outreach wave instead of a prerequisite: run the normal Prospects sourcing + cold-touch cadence, and offer the free-pilot deal to the first A-priority responder who seems like a good testimonial fit (established, well-reviewed, comfortable being recorded). Also worth a low-cost parallel path: ask around your own network / the Parker Chamber / Nextdoor before waiting on cold outreach to produce one — a warm intro converts faster than a cold pilot offer.
