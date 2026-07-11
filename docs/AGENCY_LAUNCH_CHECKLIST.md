# JetPakt AI — Development & Launch Checklist

**Version:** 1.0 · **Owner:** Ryan (rmbrown119@gmail.com) · **Last updated:** 2026-07-11

Execution companion to [AI_AGENCY_PLAN.md](AI_AGENCY_PLAN.md). The plan explains *why* and *what*; this document is the *do-this-in-this-order* list to get from the current repo state to the first paying account. Phases run mostly sequential — where a phase can run in parallel with an earlier one, it's flagged.

**Legend:** ☑ built and pushed · ☐ to do · ⚠ blocks a later phase · ⏱ time estimate

---

## Phase 0 — Already Done (commits `7f7cb81` and `39f9b76`)

Skip this section, it's for reference — every box is already checked in the repo.

- ☑ FastAPI backend rewritten: `main.py`, `api/routes/services.py`, `api/routes/webhooks.py`
- ☑ `GET /api/services` returns the 5-service catalog from `stripe_sync.AGENCY_PRODUCTS`
- ☑ `POST /api/webhooks/{stripe,vapi,twilio}` receivers, writing JSON artifacts to `output/`
- ☑ `stripe_sync.AGENCY_PRODUCTS` — 9 canonical products (setup + monthly pairs), lookup_keys defined
- ☑ `billing/stripe_client.py` — verifies + normalizes Stripe webhook events, DEV_MODE without live keys
- ☑ `jetpakt_cli` agency profile — `JETPAKT_PROFILE=agency` switch in `config.py`, no restaurant behavior changed
- ☑ Marketing site (`site/index.html`) rebranded to JetPakt AI, pricing/services/CTA
- ☑ Dead bookkeeping-marketplace code deleted (`marketplace/`, `verification/`, `stripe/`, `api/routes/marketplace.py`, `tests/test_marketplace.py`)
- ☑ Fixed `stripe/` package name shadowing the pip `stripe` package
- ☑ 12 passing tests covering backend + profile split + restaurant-fixture regression
- ☑ README, `docs/PRODUCT.md`, `docs/AI_AGENCY_PLAN.md` reconciled with what's built

---

## Phase 1 — External Account Setup (⏱ 1–2 days work, 2–3 weeks blocked on Twilio)

Do all four in parallel — most have a wait window.

### 1.1 Twilio ⚠ (blocks SMS launch, 2–3 week lead time on A2P)
- ☐ Create Twilio account, buy first US local number (~$1.15/mo) in a 720 area code
- ☐ Start A2P 10DLC brand registration (JetPakt AI as the brand, $4 one-time)
- ☐ Register a first campaign (Low-Volume Standard, $10/mo) — even one placeholder is fine to start the clock
- ☐ Point SMS status callback + inbound webhook at `https://<your-deployed-host>/api/webhooks/twilio`

### 1.2 Vapi ⚠ (blocks phone launch, no external wait)
- ☐ Create Vapi account, connect the Twilio number from 1.1
- ☐ Build one demo agent for a fake plumber ("Parker Plumbing Co") — voice, opening line, calendar-booking function
- ☐ Point the "call ended" webhook at `https://<your-deployed-host>/api/webhooks/vapi`
- ☐ **Compliance opening line:** the agent's first sentence must include *"Calls are recorded for quality — is that OK?"* (Colorado two-party consent) and *"Is it OK if we text you a confirmation?"* (TCPA opt-in capture)

### 1.3 Stripe (blocks paid onboarding, no external wait)
- ☐ In the Stripe Dashboard, create **9 products** with these exact `lookup_key`s (source: `stripe_sync.AGENCY_PRODUCTS`):

| Product name | lookup_key | Price | Recurrence |
|---|---|---|---|
| AI Front Desk — Setup | `jetpakt_agency_front_desk_setup_v1` | $997 | one-time |
| AI Front Desk — Monthly | `jetpakt_agency_front_desk_monthly_v1` | $397 | monthly |
| One-Page Site + GBP — Setup | `jetpakt_agency_site_gbp_setup_v1` | $497 | one-time |
| One-Page Site + GBP — Monthly | `jetpakt_agency_site_gbp_monthly_v1` | $97 | monthly |
| Review Autopilot — Monthly | `jetpakt_agency_review_autopilot_monthly_v1` | $197 | monthly |
| Lead Intake — Setup | `jetpakt_agency_lead_intake_setup_v1` | $297 | one-time |
| Lead Intake — Monthly | `jetpakt_agency_lead_intake_monthly_v1` | $147 | monthly |
| AI Front Desk Complete — Setup | `jetpakt_agency_bundle_setup_v1` | $1,997 | one-time |
| AI Front Desk Complete — Monthly | `jetpakt_agency_bundle_monthly_v1` | $497 | monthly |

- ☐ Copy each resulting **product ID** (`prod_...`) into `jetpakt_cli/config.py`'s `"agency"` profile → `stripe_product_tier` dict, as `product_id → (tier_label, cadence_days, mrr_usd)`. For setup fees use `cadence_days=None, mrr_usd=0`. For monthlies use `cadence_days=30, mrr_usd=<amount>`.
- ☐ Add a Stripe webhook endpoint pointing at `https://<your-deployed-host>/api/webhooks/stripe`, subscribed to `customer.subscription.created`, `customer.subscription.updated`, `checkout.session.completed`
- ☐ Copy the signing secret into `STRIPE_WEBHOOK_SECRET` env var on the deployed backend

### 1.4 Google Sheet CRM
- ☐ Create a new Google Sheet titled "JetPakt AI CRM"
- ☐ Add 4 tabs with the exact schemas in [AI_AGENCY_PLAN.md §5](AI_AGENCY_PLAN.md#5-free-crm-retargeted-jetpakt_cli-engine-not-a-new-build): `Prospects` (26 cols), `Outreach Log` (16 cols), `Suppression` (6 cols), `Clients` (18 cols)
- ☐ Grab the sheet ID (from the URL) and each tab's `gid` (from `...#gid=X` when that tab is active)
- ☐ Paste into `jetpakt_cli/config.py`'s `"agency"` profile — `sheet_id` and the four `worksheet_ids` entries — OR set `JETPAKT_AGENCY_SHEET_ID` env var and leave the code default
- ☐ Share the Sheet with whatever Google service account handles the Sheets API writes (edit access)

### 1.5 Liability rider (do this before the first paid contract)
- ☐ Call whoever writes the current LLC's business policy, add an E&O / cyber-liability endorsement covering call recording + PII storage. This is the only Phase 1 item that can happen *after* the first pilot but *must* happen before you invoice a paid customer.

---

## Phase 2 — Deploy the Backend (⏱ half a day)

Needed for every webhook URL in Phase 1 to actually work.

- ☐ Pick a host with a stable public URL: **Render** (free hobby tier), Fly.io, or Railway. Recommendation: Render — simplest zero-config Python deploy, tolerable free-tier cold starts for webhook workloads.
- ☐ Add a `Procfile` (Render doesn't need one but Fly does): `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
- ☐ Configure env vars: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `JETPAKT_PROFILE=agency`, `JETPAKT_AGENCY_SHEET_ID` (if using env-var route)
- ☐ Deploy from `main` branch (or set up auto-deploy from `claude/ai-agency-local-marketplace-5wcgb7` if you want to keep merging into the branch this ships from)
- ☐ Smoke-test `GET https://<your-host>/api/health` returns `{"status":"ok"}` and `GET /api/services` returns the 5-service catalog
- ☐ Go back and paste this host URL into the Vapi/Twilio/Stripe webhook fields from Phase 1

---

## Phase 3 — Demo Assets (⏱ 1–2 days, runs in parallel with Phase 1's Twilio wait)

You need something to show on a discovery call before you ever get on one.

- ☐ Build 3 per-vertical one-page site templates: `templates/plumber.html`, `templates/salon.html`, `templates/roofer.html` — same skeleton as `site/index.html`, different vertical-specific copy, click-to-call + click-to-text + booking placeholder
- ☐ Stand up 3 demo instances: `demo-plumber.gojetpakt.com`, `demo-salon.gojetpakt.com`, `demo-roofer.gojetpakt.com` — subdomains on gojetpakt.com pointing at the same Render host, with a route handler serving the right template based on subdomain
- ☐ Record a 60-second Loom for each vertical: caller dials the demo Twilio number, AI answers, books an appointment, texts a confirmation. Show the calendar entry appearing live.
- ☐ Write the discovery-call script (30 min): the 5 questions in [AI_AGENCY_PLAN.md §6.2](AI_AGENCY_PLAN.md#62-discovery-call-30-min)
- ☐ Draft the shared-Google-Doc proposal template (never a PDF — you want them to comment inline) with: your Loom link, the plan they'd start on, install-week schedule, 30-day money-back guarantee

---

## Phase 4 — Sales Machinery (⏱ 1 day, needs Phase 1.4 done first)

- ☐ Places API key + a small sourcing script that scans the zip ring for a given vertical, filters `website is null OR website contains 'facebook.com'`, dedupes against the `Prospects` tab, and produces `output/sourcing/<vertical>_<date>.json` for review before writing to Sheets
- ☐ Load 200 seed leads into `Prospects` covering the A-priority verticals in the core zip (80134 / 80138) — plumbers, roofers, HVAC, salons/barbers
- ☐ Write agency-vertical cold-outreach templates for `jetpakt_cli` — one per vertical, matching the smoke-gate requirements (Parker postal address present, `gojetpakt.com` present, one Ryan signature block, no em-dashes in author copy, no `scrape`/`crawl` language). Save under `output/outreach/<wave>/`.
- ☐ Run `JETPAKT_PROFILE=agency ./jetpakt smoke output/outreach/<wave>` and fix any gate failures before the templates are considered ready

---

## Phase 5 — Free Pilot Install (⏱ 1 install week, ~4–6 hours actual labor)

First real end-to-end run. See [AI_AGENCY_PLAN.md §6.3](AI_AGENCY_PLAN.md#63-install-week-5-business-days) for the day-by-day.

- ☐ Identify the first pilot business — could be a warm intro through the Parker Chamber / Nextdoor / your own network, or the first A-priority responder from Phase 4 outreach. No setup fee, first month free, in exchange for a 60-90 second video testimonial
- ☐ Discovery call → draft `Clients` row → send Loom recap within 2 hours
- ☐ **Day 1:** contract signed via Stripe (zero-dollar for the free pilot — use a 100%-off coupon on the bundle setup and first month), GBP manager access granted
- ☐ **Day 2:** provision a second Twilio number for this client, configure their Vapi agent (their business name, hours, service list, escalation cell), calendar OAuth
- ☐ **Day 3:** deploy their one-page site, update GBP with new website + hours
- ☐ **Day 4:** approve Review Autopilot SMS templates with the owner (must not gate/incentivize — see [AI_AGENCY_PLAN.md §9](AI_AGENCY_PLAN.md#9-legal--compliance-landmines-dont-skip))
- ☐ **Day 5:** live walkthrough call, flip call-forwarding on, owner keeps direct number for regulars
- ☐ Record post-install testimonial + before/after numbers (missed-call baseline vs. Day-1 booked-count)

---

## Phase 6 — First 5 Paying Accounts (⏱ 3–4 weeks)

- ☐ Run outreach cadence at 500 new leads/week: SMS day 3, email day 7, drop-in day 14 for A-priority core-zip
- ☐ Add the pilot's testimonial + numbers to the marketing site (`site/index.html` — add a "case study" section under the pricing grid) and the discovery-call script
- ☐ Target: 5 paid `AI Front Desk Complete` bundle installs in the 80134 core zip
- ☐ After paid install #3, record a case-study Loom with real numbers (calls answered, bookings created)
- ☐ Confirm the 30-day money-back guarantee is documented in the Stripe checkout terms and in every proposal

---

## Phase 7 — Ongoing Ops (starts at 5 accounts, never ends)

Not a launch step — a "make sure these keep running" list.

- ☐ Weekly automated summary email to each client: calls answered, bookings created, reviews received (send as a `jetpakt_cli` outreach wave, or write a small `weekly_summary.py` cron)
- ☐ Monthly 15-min tune-up call for the first 90 days of every account, then quarterly
- ☐ Same-day owner call on any month with >30% call-volume drop or a new 1-star review
- ☐ Watch `output/onboarding/` for `status: "unconfigured"` — those are Stripe webhook events for products not yet in `STRIPE_PRODUCT_TIER`. Fix by adding the product ID to config; the plan resends on the next Stripe webhook.
- ☐ At ~10 accounts: move escalation from your personal cell to a shared on-call number (Google Voice, or a second Twilio line forwarded to you)
- ☐ At ~20 accounts: hire one part-time VA ($8–12/hr) for lead sourcing + first-touch SMS on the outreach wave

---

## Dependency Graph (what blocks what)

```
Phase 0 (done) ─┬─> Phase 1.1 Twilio ─────┐
                ├─> Phase 1.2 Vapi ───────┼─> Phase 2 Deploy ─> Phase 5 Pilot ─> Phase 6 First 5
                ├─> Phase 1.3 Stripe ─────┤        ▲
                ├─> Phase 1.4 Sheet ──────┘        │
                └─> Phase 3 Demo (parallel) ───────┤
                                                    │
                              Phase 4 Sales ────────┘
                              (needs 1.4 Sheet)
```

Twilio A2P is the longest external wait — start Phase 1.1 today, regardless of anything else.

---

## What "Launch" Means

**Soft launch** = Phase 5 complete (one free pilot, live, testimonial recorded).
**Full launch** = Phase 6 complete (first 5 paid accounts on `AI Front Desk Complete`, ~$2.5k MRR, 30-day guarantee holding).

Neither is Day 1. Both are 6–8 weeks out from the start of Phase 1, gated on Twilio A2P and finding the first pilot business.
