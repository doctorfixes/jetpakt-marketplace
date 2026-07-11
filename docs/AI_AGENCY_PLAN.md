# AI Agency Automation Plan — 80134 Local Small Business

**Version:** 1.0 (planning) · **Owner:** Ryan (rmbrown119@gmail.com) · **Date:** 2026-07-11

You are the operator. This document specs the full pivot from JetPakt (bookkeeping marketplace) to a single-operator AI Agency serving local trades and service businesses in and around Parker, CO (80134). Delivery starts in a new repo; JetPakt stays as-is and gets archived once the pivot ships.

---

## 1. Positioning

**Name (placeholder):** Front Desk AI · Parker
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
- Single Next.js page on the agency's shared Vercel account (client owns the domain)
- Services, hours, service area, click-to-call, click-to-text, embedded booking
- Full GBP claim, category cleanup, photo upload, service list, Q&A seeding
- **Setup:** $497 one-time · **Monthly:** $97 (hosting + monthly GBP posts + edits)

### S3 — Review Autopilot
- Post-job SMS asks for a Google review with a deep link
- Owner-approved templates per service (salon vs. plumber wording differs)
- Weekly summary of new reviews + one-tap owner reply drafts
- **Add-on to any bundle:** $147/mo · **Standalone:** $197/mo

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

## 4. Tech Stack (new repo)

**Repo name:** `frontdesk-ai` (in a new GitHub repo — JetPakt stays put)

| Layer | Choice | Why |
|---|---|---|
| Marketing site | Next.js 15 + Tailwind on Vercel | Free tier fits, per-client sites deploy as subprojects |
| Backend API | Next.js Route Handlers + one small FastAPI service on Render (webhooks, cron) | Free hobby tier on both; Python is fine here since you already have FastAPI experience from JetPakt |
| AI voice | **Vapi** (primary) with Retell fallback | $0.05–0.07/min all-in, GPT-4o-mini or Claude Haiku, sub-second latency, Twilio numbers built in |
| SMS | Twilio (needs A2P 10DLC registration — start now, takes 2–3 weeks) | Standard for US business SMS; ~$0.008/msg |
| Booking | **Cal.com** self-hosted (free) or Google Calendar direct via API | Cal.com if client wants a nice public page; Calendar API if they just want writes |
| Website generation | Templated Next.js `[slug]` page pulling from Sheets/Airtable | One template, per-client data row, deploy on push |
| CRM | **Google Sheets + Apps Script** (see §5) | Zero cost, you and any VA can read it, wires to backend via webhooks |
| Payments | Stripe (subscription + one-time setup fee product) | You already have Stripe integrated in JetPakt — port the client + webhook handler |
| Reviews | GBP deep link via SMS; GBP API for reads only (write access is restricted) | Google won't let 3rd parties post reviews on behalf of customers, so SMS-with-link is the only compliant path |
| Client portal | Same Next.js app, `/client/[slug]` route with magic-link auth | Owners see call transcripts, upcoming bookings, review status |
| Observability | Vercel logs + Axiom free tier | Enough for first 100 accounts |

**Hard "do not build" list (buy or skip, don't roll your own):** voice model, SMS carrier, calendar UI, review posting.

---

## 5. Free CRM: Google Sheets + Apps Script

One Google Workbook, six tabs. Every row is keyed by `id` (Apps Script `Utilities.getUuid()`). The FastAPI backend reads/writes via a service-account and the Sheets API.

### Tabs and columns

**`leads`** — every business you're targeting, sourced or inbound
```
id | source | business_name | vertical | address | zip | phone | website | gbp_url
| owner_first | owner_last | owner_email | last_touched_at | status
| next_action | next_action_at | notes
```
`status ∈ {new, researched, contacted, replied, meeting_set, proposal_sent, won, lost, do_not_contact}`

**`accounts`** — leads that converted; one row per paying business
```
id | lead_id | business_name | vertical | address | zip | primary_phone
| forwarded_number | stripe_customer_id | plan | mrr | setup_paid_at
| activated_at | health_score | csm_notes
```

**`services`** — which services each account has active
```
id | account_id | service_code | started_at | ended_at | monthly_price | status
```
`service_code ∈ {front_desk, site_gbp, review_autopilot, lead_intake}`

**`calls`** — every AI phone interaction (written by Vapi webhook → backend → Sheets)
```
id | account_id | started_at | duration_sec | caller_phone | outcome
| booked_appt_id | escalated | transcript_url | cost_usd
```
`outcome ∈ {booked, quoted, callback, spam, escalated, hangup}`

**`bookings`** — appointments created via the AI
```
id | account_id | call_id | customer_name | customer_phone | service | start_at | notes | status
```

**`reviews_out`** — review requests sent
```
id | account_id | booking_id | sent_at | responded | left_review | review_url
```

### Apps Script automations (all in `Code.gs` in the workbook)

1. **Daily 8am pipeline digest** — sum `leads` by status, `accounts` by health, list overdue `next_action_at`; email you a plain-text summary.
2. **Auto-set `next_action_at`** on status change:
   - `contacted` → +3 days
   - `replied` → +1 day
   - `proposal_sent` → +5 days
3. **Backend webhook receiver** — a `doPost(e)` endpoint the FastAPI backend hits after each Vapi call or Stripe event; appends to `calls` / updates `accounts`.
4. **Weekly Sunday churn scan** — accounts where `calls` count in the last 7 days is 0 and status = active → flag for check-in.
5. **Setup-fee unpaid nag** — accounts where `setup_paid_at` is null and `activated_at` is set → weekly email until paid.

**Backup:** Apps Script triggers a nightly export of the whole workbook to a Drive folder as `.xlsx`. Keeps 30 rolling copies.

### Why not Airtable / HubSpot?
- **Airtable free** caps at 1,000 records/base. First outreach batch alone will fill that.
- **HubSpot free** has deal pipelines, but its API rate limits and rigid object model fight the "one row is one lead, edit inline in a VA-friendly grid" workflow. Fine to graduate to it at ~$5k MRR.

---

## 6. Sales & Delivery Process

### 6.1 Outreach (weeks 1–ongoing)
1. **Sourcing:** run a Places API scan of the zip ring for each vertical, filter for `website is null OR website contains 'facebook.com'`, dedupe against `leads`. Target: 500 new rows/week.
2. **First touch:** 15-second personalized voicemail + follow-up SMS ("Saw you don't have a booking page — mind if I send a 60-sec Loom of what I built for a Parker plumber?"). Human-recorded voicemail per vertical, not AI — feels wrong and hurts trust on trades.
3. **Follow-up cadence:** SMS day 3, email day 7, drop-in visit day 14 for A-priority verticals in the core zip.
4. **Close artifact:** shared Google Doc proposal (never a PDF — you want them to be able to comment) linking a Loom of a live demo installed on `demo-{vertical}.frontdeskai.local`.

### 6.2 Discovery call (30 min)
- What's your current phone situation? (Answer service? Voicemail? Personal cell?)
- How many calls/day roughly? What % do you miss?
- Where do bookings live today? (Paper book, Google Cal, Square, Vagaro?)
- What's your Google review count and star rating?
- Who owns the current website (if any) and the GBP login?

Output: filled-in `accounts` row draft + a Loom recap sent within 2 hours.

### 6.3 Install week (5 business days)
- **Day 1:** Contract signed via Stripe checkout ($setup + first month's $mo). GBP ownership transferred or manager access granted. Domain access confirmed.
- **Day 2:** Vapi agent configured — voice, script, escalation number, calendar OAuth. Twilio number provisioned and forwarded to.
- **Day 3:** One-page site deployed to `{business}.com` or a `frontdeskai.co/{slug}` fallback. GBP updated with new website + hours.
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
- [ ] Spin up `frontdesk-ai` repo (Next.js + FastAPI cron worker skeleton)
- [ ] Stripe account with two products (Setup fee, Monthly bundle) — port the Stripe client from JetPakt
- [ ] Vapi account, one demo agent for a fake plumber
- [ ] Twilio account, kick off A2P 10DLC registration (blocks for 2–3 weeks — start now)
- [ ] Google Workspace + Sheets CRM workbook with all six tabs and daily digest Apps Script
- [ ] Buy `frontdeskai.co` (or chosen brand domain)

### Days 8–21: Demo assets and 1st design partner
- [ ] Build the templated one-page site with 3 vertical variants (plumber, salon, roofer)
- [ ] Record 3 vertical-specific Loom demos on the demo numbers
- [ ] Source 200 leads into `leads` tab from the core zip
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

## 10. What Happens to the JetPakt Code

Since we're doing a full rewrite in a new repo, this repo (`jetpakt-marketplace`) stays where it is. Two options once the new agency is live:
1. **Archive** the JetPakt repo on GitHub (read-only, keeps the URL alive).
2. **Salvage list** — before archiving, port these to `frontdesk-ai`:
   - `stripe/escrow.py` → generic Stripe client (rename module, drop the escrow-specific bits)
   - `main.py` FastAPI app skeleton + health check
   - `docs/OUTREACH_TEMPLATES.md`, `docs/PRICING_MODEL.md`, `docs/ROI_MODEL.md` — the frameworks apply, the numbers don't
   - `netlify.toml` deploy pattern (or move to Vercel — recommended)

Nothing in `marketplace/`, `verification/`, or `api/routes/marketplace.py` is worth porting — that's all bookkeeping-domain logic.

---

## 11. Open Questions to Decide Before Day 1

1. **Brand name:** "Front Desk AI · Parker" is a placeholder. Prefer something geo-neutral if you plan to expand past the Denver metro?
2. **Legal entity:** existing LLC to invoice through, or set up a new one for liability separation from JetPakt?
3. **Cell number for owner escalations:** yours during the pilot, or set up a shared on-call number from day one?
4. **Free-pilot design partner:** do you already have one warm business owner in the 80134 area who'd say yes to a free install for a testimonial? If yes, name them — it changes the day-7 timeline.
5. **Domain:** `frontdeskai.co`, `parkerfrontdesk.com`, something else?

Answer these and days 1–7 becomes concrete tickets, not a plan.
