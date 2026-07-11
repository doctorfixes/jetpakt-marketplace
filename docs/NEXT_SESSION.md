# Next Session Handoff — JetPakt AI

**Last session ended:** 2026-07-11 · **Branch:** `claude/ai-agency-local-marketplace-5wcgb7` · **Head commit:** `5ca91a8`

## Read First (2 minutes, in order)

1. `docs/AI_AGENCY_PLAN.md` — strategy, positioning, pricing, target market, compliance. Explains *why*.
2. `docs/AGENCY_LAUNCH_CHECKLIST.md` — 8-phase execution plan. Phase 0 is done; Phase 1 blocks on Ryan; Phases 3 and 4 are what a fresh session can build without him.
3. This file — what to pick up first.

## Where We Left It

The AI Agency pivot is code-complete on Phase 0 (see the checklist). What's *not* done falls into two buckets:

- **Blocked on Ryan** (external account signups Claude can't do): Phase 1 (Twilio, Vapi, Stripe products, Google Sheet), Phase 2 (deployment), Phase 5 (pilot install), Phase 6 (paid accounts).
- **Buildable right now** (no external account required): Phase 3 (demo assets), Phase 4 (sales machinery). This is the queue.

## Pick Up Here (do these in order)

### Task A — Build the 3 vertical demo site templates ⏱ ~3 hours

**Goal:** per-vertical one-page templates Ryan can show on a discovery call before he's signed up a single client. Same skeleton as `site/index.html`, different copy per vertical.

Create:
- `site/demo/plumber.html` — "Parker Plumbing Co" as the fake business. Copy pattern: emergency service, licensed & insured, 24/7 dispatch, service list (drain clear, water heater, leak repair, sump pump). CTA: "Call for emergency service" click-to-call button + a booking form placeholder wired to a `#booking` anchor.
- `site/demo/salon.html` — "Parker Cuts & Color". Copy pattern: services (cut, color, balayage, keratin), stylist bios placeholder, online booking. CTA: "Book online 24/7."
- `site/demo/roofer.html` — "Parker Roofing Co". Copy pattern: hail damage inspection (Parker/Douglas County is on the hail belt — this is the local hook), insurance claim assistance, storm response, free inspection. CTA: "Schedule a free inspection."

Add a FastAPI route (`api/routes/demo.py`, new) that serves the right template based on a `{vertical}` path parameter or a subdomain header. Route pattern: `GET /demo/{vertical}` returning the matching HTML file. Wire into `main.py`. Write a test: `tests/test_demo.py` — `GET /demo/plumber` returns 200 with "Parker Plumbing Co" in the body, `GET /demo/unknown` returns 404.

**Watch for:** the marketing site is mounted with StaticFiles at `/` (`main.py:47`), which will greedy-match `/demo/...` too. Register the demo router *before* the static mount so its routes win. Test both routes work after the change.

### Task B — Places API sourcing script for Phase 4 ⏱ ~2 hours

**Goal:** given a vertical and a list of zips, produce a `output/sourcing/<vertical>_<date>.json` file of candidate businesses that don't have a website, in the `Prospects` row shape `jetpakt_cli` already expects. Human-in-the-loop step: Ryan reviews the JSON before it's applied to the Sheet, same offline-plan pattern as everything else in `jetpakt_cli/`.

Create `jetpakt_cli/sourcing.py` and wire a `jetpakt source-leads --vertical plumber --zips 80134,80138 [--limit 200]` command in `cli.py`. Filter: `website is null OR website contains 'facebook.com'`. Output row shape must match the 26-column `Prospects` schema documented in `AI_AGENCY_PLAN.md §5`.

Two implementation notes:
- **Do not call the Places API from inside the CLI.** Same pattern as `stripe_sync.py`'s `_call` shim (`stripe_sync.py:87`) and `jetpakt_cli/README.md:69`: the CLI is deterministic and offline. It takes a normalized `places_hits.json` input file (agent fetches raw hits via the Places connector, hands the normalized file to the CLI) and produces the sourcing plan output. This lets the CLI stay tested and re-runnable without API keys.
- **Dedupe against the existing `Prospects` tab** before writing new rows. Take a `--existing-prospects <file.json>` arg like `enrich.py` already does, and drop hits whose `google_url` or normalized business_name+zip already exists.

Fixtures + tests: add `jetpakt_cli/tests/fixtures_places_agency_hits.json` (2–3 fake plumbers, one already-in-Sheet dupe, one Facebook-only). Add `tests/test_sourcing.py` covering: happy path (unique lead written), dedupe (existing not re-written), Facebook filter (skipped).

### Task C — Agency-vertical cold-outreach templates ⏱ ~2 hours

**Goal:** 3 outreach draft `.md` files (one per A-vertical) under `output/outreach/agency_wave_001/` that pass every smoke gate in `jetpakt_cli/smoke.py`. Follows the same draft format `jetpakt_cli.smoke.check_draft` expects.

Reread `jetpakt_cli/smoke.py:53–83` for the 10 gates. Key requirements each draft must hit:
- Subject ≤45 chars
- Body excludes `denver` (weird but true — restaurant-era gate still on)
- No em/en-dashes outside verbatim quote lines
- The literal string `"6222 E Pine Lane, Suite 6212, Parker, CO 80138"` appears once
- The literal string `"Ryan B., JetPakt Solutions"` appears exactly once
- A verbatim quote block (line starting with `    "`)
- No `scrape`/`crawl` language
- `gojetpakt.com` appears
- No LEGAL-HIGH mapping (restaurant-only gate, doesn't apply to agency drafts)

Run `JETPAKT_PROFILE=agency ./jetpakt smoke output/outreach/agency_wave_001` after writing — must show all PASS. If any draft fails, fix the draft, don't loosen the gate.

Verbatim-quote-block content suggestion: use a real Google review of the target business's category (e.g., a public review of *another* Parker plumber saying "I called 4 places, none picked up") — that's the setup for the pitch, not a claim about the target business. Keeps you defensible.

### Task D — Add a `case_studies` placeholder to the marketing site ⏱ ~30 min

`site/index.html` has no "proof" section yet. Add an empty `<section id="case-studies">` between the "Pick What You Need" and pricing sections, with a comment `<!-- populate after first paid install per AGENCY_LAUNCH_CHECKLIST.md Phase 6 -->`. This unblocks the "add testimonial after install #3" step in Phase 6 — the slot's there, just needs content.

## What NOT To Touch

- **`jetpakt_cli/config.py` restaurant profile** — those are live Sheet ID / Stripe product IDs for the JetPakt Pulse business. `tests/test_jetpakt_cli_profiles.py` will fail loudly if you break it.
- **Any of the restaurant docs** (`ONBOARDING_PLAYBOOK.md`, `PULSE.md`, `ROS_FRAMEWORK.md`, `REPOSITION_V3_SPEC.md`, `PRICING_MODEL.md`, `ROI_MODEL.md`, `COMPETITIVE_ANALYSIS.md`, `OUTREACH_TEMPLATES.md`, `GUARDRAILS.md`, `EMAIL_SETUP.md`, `OUTREACH_FREE_PILOT.md`, `BILLING.md`, `competitor_matrix.csv`) — all describe the live restaurant business, none are stale.
- **The two remaining open questions in `AI_AGENCY_PLAN.md §11`** (legal entity #3, on-call number #4, pilot partner #5 — Ryan already said "unsure" and defaults are documented). Don't reopen them.

## Blocked on Ryan (report at end of next session)

If any of these have completed since this handoff was written, unblock the corresponding checklist phase:

- ☐ Twilio account + A2P 10DLC registration started (Phase 1.1 — 2–3 week wait clock)
- ☐ Vapi account + demo plumber agent (Phase 1.2)
- ☐ Stripe products created with the 9 lookup_keys in `AGENCY_LAUNCH_CHECKLIST.md` Phase 1.3
- ☐ Google Sheet CRM created + `sheet_id`/`worksheet_ids` filled into `jetpakt_cli/config.py`'s agency profile (Phase 1.4)
- ☐ Backend deployed to Render/Fly with a stable public URL (Phase 2)

## How To Continue

If a fresh session picks this up:
1. `git checkout claude/ai-agency-local-marketplace-5wcgb7 && git pull`
2. Read the three docs in the "Read First" section at the top
3. Start with Task A (demo templates) unless Ryan has said otherwise
4. Commit each task separately with a message tied to Phase/Task labels for easy diff review
5. Run `python3 -m pytest tests/ -v` before committing anything — 12 tests pass at commit `5ca91a8`, new tasks should keep that count going up

If Ryan picks it up in this session, no re-context needed — he was here.
