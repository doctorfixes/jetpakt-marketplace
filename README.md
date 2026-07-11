# JetPakt AI — AI Front Desk for Local Service Businesses

24/7 AI phone answering, booking, a real website, and automatic review requests for salons, dry cleaners, roofers, plumbers, and other trades that don't have any of this today. Built and operated by Ryan out of Parker, CO, targeting 80134 and the surrounding south-metro Denver zips.

[gojetpakt.com](https://gojetpakt.com) — built by [doctorfixes](https://github.com/doctorfixes)

See [docs/AI_AGENCY_PLAN.md](docs/AI_AGENCY_PLAN.md) for the full business plan (target list, sales process, pricing, milestones, legal landmines).

---

## What This Repo Runs

JetPakt runs more than one business line on the same underlying tooling:

- **JetPakt AI** (this pivot) — the AI Front Desk agency for local trades/service businesses. New, no live Stripe products yet.
- **JetPakt Pulse** — an existing, separate restaurant-reputation business (Denver metro). Its Google Sheet and Stripe products are live; nothing about it changed as part of this pivot.

Both share the same CRM/outreach mechanism (`jetpakt_cli/`) via a **profile switch** — see below.

## Service Catalog

| Service | Setup | Monthly |
|---|---|---|
| AI Front Desk (24/7 phone answering + booking) | $997 | $397 |
| One-Page Site + Google Business Profile | $497 | $97 |
| Review Autopilot | — | $197 |
| Lead Intake & Instant Quote | $297 | $147 |
| **AI Front Desk Complete** (bundle) | **$1,997** | **$497** |

Source of truth for pricing: `stripe_sync.AGENCY_PRODUCTS` in `stripe_sync.py`, served live at `GET /api/services`.

## Quick Start

```bash
# Install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn main:app --reload

# Visit
#   API:      http://localhost:8000/api/health
#   Services: http://localhost:8000/api/services
#   Docs:     http://localhost:8000/docs
#   Site:     http://localhost:8000/
```

## Project Structure

```
main.py               # FastAPI entrypoint — services catalog, webhooks, static site

api/routes/
├── services.py        # GET /api/services — the AI Agency catalog
└── webhooks.py         # Stripe / Vapi / Twilio inbound webhooks

billing/
└── stripe_client.py   # Verifies + normalizes Stripe webhook events (DEV_MODE without a webhook secret)

stripe_sync.py          # Canonical product catalog (restaurant + agency), read-only Stripe sync

jetpakt_cli/            # CRM + outreach engine — dual-profile (restaurant | agency), see below
├── config.py            # JETPAKT_PROFILE switch: Sheet ID, Stripe tiers, welcome copy per profile
├── clients.py            # Stripe customer/subscription -> Clients-tab onboarding plan
├── enrich.py             # Places-rating + Hunter-email enrichment plans
├── inbox.py               # Reply/bounce classification for the cold-outreach inbox scan
├── smoke.py                # Hard gates every outreach draft must pass before sending
├── sync.py                  # Draft -> Outreach Log row + Sheet sync plan
├── outlook.py                 # Draft -> Outlook draft_email plan
└── cli.py                      # `./jetpakt <command>` — see jetpakt_cli/README.md

site/
└── index.html            # Marketing site (gojetpakt.com)

docs/
├── AI_AGENCY_PLAN.md      # Full business plan for the AI Agency pivot
└── ...                     # Restaurant-business docs (ROS_FRAMEWORK, PRICING_MODEL, etc.) — unchanged
```

## The CRM/Outreach Engine Is Shared, Not Duplicated

`jetpakt_cli/` already implements a working cold-outreach → CRM → onboarding pipeline for the restaurant business (Google Sheets: Prospects / Outreach Log / Suppression / Clients tabs, Outlook drafting, Stripe-triggered onboarding, smoke-gated compliance checks). Rather than build a second CRM from scratch for the AI Agency, that engine got a **profile switch**:

```bash
./jetpakt <command>                          # restaurant Pulse (default — unchanged behavior)
JETPAKT_PROFILE=agency ./jetpakt <command>    # AI Agency (80134 trades/local-service)
```

The restaurant profile's Sheet ID and Stripe product IDs are real and live — nothing about them changed. The agency profile's Sheet/Stripe fields are empty placeholders until you create them (same "billing/CRM writes require a human step" rule `stripe_sync.py` already follows for the restaurant business — see `docs/AI_AGENCY_PLAN.md` §5 for the Sheet tab schema to create).

## API Endpoints

- `GET /api/health` — health check
- `GET /api/services` — the AI Agency service catalog (setup + monthly pricing per service)
- `GET /api/services/{code}` — single service detail
- `POST /api/webhooks/stripe` — subscription created/updated + checkout completed → writes an onboarding plan JSON (via `jetpakt_cli.clients.build_onboarding_plan`) for review/apply, same pattern the CLI uses everywhere else
- `POST /api/webhooks/vapi` — AI phone call events → call log JSON
- `POST /api/webhooks/twilio` — SMS status/inbound → SMS log JSON

None of the webhook handlers write to Sheets, Outlook, Twilio, or Vapi directly — they normalize and drop a JSON artifact under `output/` for a human (or the agent, via connectors) to review and apply. Same rule as the rest of the codebase: no automated sends.

## Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload      # http://localhost:8000/docs
pytest tests/ -v                # backend + CRM-profile regression tests
```

## Deployment

- **Marketing site**: Deploys to Netlify from `site/` → gojetpakt.com
- **API backend**: FastAPI app, deployable as Netlify Functions or standalone service
- **Stripe**: Set `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` env vars for production; without them the backend runs in DEV_MODE (webhook signature checks skipped, no live Stripe calls)

## License

MIT
