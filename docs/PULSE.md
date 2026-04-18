# JetPakt Pulse — Recurring Insights Program

**What it is.** Pulse is the subscription layer on top of the one-time Scan. Every week (or every month, depending on tier), Pulse re-samples each client's public reputation signals, diffs the new snapshot against the prior one, and produces a short PDF digest plus a pre-composed Outlook draft. The draft never auto-sends — Ryan reviews and clicks send.

**Why it exists.** The one-time Scan delivers the diagnosis. Pulse is the reason clients pay month after month: an auditable record that shows what moved, what to do about it, and a continuous pressure to execute the ROS action plan. It also catches material changes (a rating drop, a new legal-HIGH flag, a widening peer gap) early enough to matter.

## Economic guardrails

- **Draft-only.** No autonomous email sends, ever.
- **Per-account approval.** Each cycle produces a reviewable `.md` preview; Ryan decides per draft.
- **Two-lane routing.** Legal-HIGH items and overall HIGH cycles route to Ryan only; everything else can route client-direct (with Ryan CC'd) per account default.
- **No individual names.** Structural copy uses "team"; reviewer names only appear inside verbatim quotes in the attached PDF.
- **Cost-bounded.** Each cycle is one scan call + one PDF render + one JSON snapshot per account. No LLM in the hot path.

## Pieces

| File                           | Role                                                                                                           |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| `data/accounts.yaml`           | Account roster — id, tier, cadence, scan module + function, delivery mode, emails.                             |
| `pulse_engine.py`              | Snapshot, diff, escalation. Returns `PulseInsight`.                                                            |
| `pulse_report.py`              | Renders `PulseInsight` → 1-page PDF (reuses `scan_pdf` fonts + palette).                                       |
| `pulse_deliver.py`             | Composes Outlook draft payload (subject, To/CC, HTML body, attachment) + writes `.md` preview to disk.         |
| `pulse_cron.py`                | CLI entry point. Runs one or all accounts for a cadence. What the scheduler calls.                             |
| `data/snapshots/{account}/`    | JSON snapshots, one per cycle. Source of truth for diffs.                                                      |
| `output/pulse/`                | Rendered PDFs + `drafts/` previews + `pulse_runs.jsonl` audit log.                                             |

## Running

```bash
# Weekly cadence (all Tier-3+ accounts)
python pulse_cron.py --cadence weekly

# Monthly cadence (all Tier-2+ accounts)
python pulse_cron.py --cadence monthly

# One specific account, any cadence
python pulse_cron.py --account big_daddys_colfax

# Dry run (diff only — no PDFs, no drafts)
python pulse_cron.py --cadence weekly --dry-run
```

## Material-impact thresholds

From `pulse_engine.THRESHOLDS`:

| Key                    | Value | Meaning                                                                        |
| ---------------------- | ----- | ------------------------------------------------------------------------------ |
| `rating_informational` | 0.05  | Below this = noise; ignored in the diff.                                       |
| `rating_medium`        | 0.10  | MED severity change.                                                           |
| `rating_high_drop`     | 0.30  | HIGH — one-period drop of ≥0.30★. Same-day alert.                              |
| `severity_medium`      | 1.00  | Signal-level severity shift of ≥1.0 points = MED change.                       |
| `peer_gap_high`        | 0.25  | Peer gap widens ≥0.25★ → HIGH same-day alert (per Ryan's alert criteria).      |
| `negative_share_high`  | 0.40  | First crossing of 40% recent-negative share → HIGH.                            |

## Cadence map (tied to pricing)

| Tier | Price       | Pulse cadence             |
| ---- | ----------- | ------------------------- |
| 1    | $49 one-off | None (scan only)          |
| 2    | $149/mo     | Monthly digest            |
| 3    | $399/mo     | Weekly digest             |
| 4    | $899/mo     | Weekly + on-alert         |
| 5    | $1,499/mo   | Weekly + on-alert + SMS   |

See `PRICING_MODEL.md` §3 for the full definition.

## Delivery routing

`pulse_deliver.build_draft()` applies these rules in order:

1. **Legal-HIGH item present.** → To: Ryan. Cc: none. `requires_human_review=True`. Reason: "Legal-HIGH item present — routed to Ryan only; client will be looped in after legal review."
2. **Overall severity = HIGH.** → To: Ryan. Cc: none. `requires_human_review=True`. Reason: "HIGH overall severity — routed to Ryan only for human review before client delivery."
3. **Account default = `client_cc_ryan` AND client email on file.** → To: client. Cc: Ryan. `requires_human_review` follows overall severity.
4. **Otherwise.** → To: Ryan. Cc: none. (Used when account has no client email yet, or explicit `ryan_only`.)

## Approval workflow

1. `pulse_cron.py` runs (scheduled or manual).
2. Each account produces: `output/pulse/{account}_{date}.pdf` + `output/pulse/drafts/{account}_{date}.md`.
3. Ryan reads the `.md` previews, starting with ones tagged `REQUIRES HUMAN REVIEW`.
4. For each draft Ryan approves, he either (a) forwards the payload to the outlook connector's `create_draft` tool, or (b) manually re-creates the draft in Outlook and attaches the PDF.
5. Cycle ends. Next cycle diffs against today's snapshot.

## Scheduling

The natural cadence is **Mondays at 07:00 MT (13:00 UTC)** — gives Ryan the workweek to clear drafts. Set up with:

```
schedule_cron create
  name: "JetPakt Pulse — weekly"
  cron: "0 13 * * 1"     # Mondays 13:00 UTC = 07:00 MT winter / 06:00 MT summer
  task: "run python pulse_cron.py --cadence weekly and summarize results"
  exact: true
```

Monthly runs on the 1st at the same time: `0 13 1 * *`.

**Cost note.** Each cycle costs one agent run + ~3s of scan/render per account. For the current 3-account pilot that's trivial. As the roster grows past ~30 accounts, move the scan calls into a parallel pool and batch the connector fetches.

## Integration with live connectors

The engine calls `_run_scan_fixture()`, which today dispatches to the in-repo scan modules (`scan_big_daddys`, `scan_hey_kiddo`, `scan_engine.westrail_scan`). When the Yelp + Google Places connectors go live, swap in the live fetch inside `_run_scan_fixture`. The rest of the pipeline (diff, report, deliver) stays unchanged.

## Tests

`tests/test_pulse.py` covers:

1. Identical snapshots produce no MED/HIGH changes (diff stability).
2. A rating drop ≥0.30★ raises a HIGH `rating_drop_*` change.
3. A new LEGAL-HIGH signal raises a HIGH change with `LEGAL-HIGH` in the description.
4. Legal-HIGH routing overrides `client_cc_ryan` → Ryan only.
5. `client_cc_ryan` routes client-direct + Ryan CC'd when no legal-HIGH and severity < HIGH.
6. Pulse body copy leaks no common first names (structural-only copy).

Run: `python -m pytest tests/test_pulse.py -q`.
