# JetPakt Billing — Stripe integration

Stripe is connected to JetPakt, LLC (`acct_1TFjC3Ea6thiGvoJ`) via a **read-only** MCP connector. The connector can retrieve products, prices, customers, subscriptions, invoices, and payment intents; it cannot create or modify them. Billing writes stay under Ryan's direct control in the Dashboard — same separation-of-concerns as Pulse drafts staying send-only.

## Catalog (manual one-time setup)

Create these in [Stripe Dashboard → Products](https://dashboard.stripe.com/products/create). The `lookup_key` is how `stripe_sync.py` and the Pulse engine find each price by name rather than by brittle IDs.

| Product name                  | Price      | Billing     | lookup_key                      | Tier |
| ----------------------------- | ---------- | ----------- | ------------------------------- | ---- |
| JetPakt Scan                  | $49.00     | one-time    | `jetpakt_scan_v1`               | 1    |
| JetPakt Pulse Essentials      | $149.00    | monthly     | `jetpakt_pulse_essentials_v1`   | 2    |
| JetPakt Pulse Pro             | $399.00    | monthly     | `jetpakt_pulse_pro_v1`          | 3    |
| JetPakt Pulse Alert           | $899.00    | monthly     | `jetpakt_pulse_alert_v1`        | 4    |
| JetPakt Pulse Concierge       | $1,499.00  | monthly     | `jetpakt_pulse_concierge_v1`    | 5    |

For each: create the product, add one price with the lookup_key shown above, set currency USD. Statement descriptors optional but recommended ("JETPAKT SCAN", "JETPAKT PULSE P", etc.).

Source of truth for the canonical list: `stripe_sync.CANONICAL_PRODUCTS`.

## Syncing the catalog into JetPakt

After the products exist in Dashboard, refresh the local cache:

```bash
# From an agent session (read API calls go through the MCP connector)
python stripe_sync.py --refresh

# View what's cached
python stripe_sync.py --show
```

Output is `data/stripe_catalog.json` — a tiny file mapping `lookup_key → {price_id, product_id, unit_amount, currency, recurring}`. Pulse reads it at billing-gate time.

## Pulse billing gate

`pulse_cron.py` now supports an optional Stripe subscription gate:

- An `Account` with both `stripe_customer_id` and `stripe_price_lookup_key` set triggers the gate.
- An `Account` missing either field runs with no gate (current behavior — preserves the demo roster).
- The gate calls `list_subscriptions` filtered to that customer + price, and allows the cycle only if a subscription is `active` or `trialing`.
- By default the gate is **log-only**: missing/lapsed subs are written to `output/pulse/billing_gaps.jsonl` but the cycle still runs. This is the safer soft-launch mode — no cycles are missed while billing is still being wired up.
- Pass `--enforce-billing` to make the gate hard: lapsed subs skip the cycle entirely.

```bash
# Soft mode (default) — runs everything, logs billing gaps
python pulse_cron.py --cadence weekly

# Hard mode — skips accounts without active subscriptions
python pulse_cron.py --cadence weekly --enforce-billing
```

## Adding a paying client

Once Ryan signs a client and creates a Stripe Customer + Subscription in the Dashboard:

1. Copy the customer ID (`cus_...`) and the price lookup_key they're on.
2. Add them to `data/accounts.yaml`:

   ```yaml
   - account_id: example_bistro
     name: Example Bistro
     tier: 3
     cadence: weekly
     scan_module: scan_example
     scan_fn: example_scan
     delivery_mode: client_cc_ryan
     client_email: owner@example.com
     ryan_email: gojetpakt.us@outlook.com
     contract_started: "2026-05-01"
     stripe_customer_id: cus_XXXXXXXXXXXXXX
     stripe_price_lookup_key: jetpakt_pulse_pro_v1
   ```

3. Run `python pulse_cron.py --account example_bistro` once to seed the baseline snapshot. Next scheduled cycle picks up the account automatically.

## Guardrails

- **Connector is read-only.** No code path in JetPakt can create a charge, issue a refund, or change a subscription.
- **Gate is log-only by default.** Soft-launch safe — no billing miswire accidentally silences a real client.
- **Catalog is cached.** Pulse never blocks on Stripe network calls — if the sync is stale or missing, the gate allows the run and logs `catalog not yet synced`.
- **Per-account opt-in.** Accounts without stripe_customer_id behave as before.

## Audit trail

- `data/stripe_catalog.json` — last-known catalog state.
- `output/pulse/billing_gaps.jsonl` — every gate check: one line per account per cycle with allowed flag, reason, subscription status.
- `output/pulse/pulse_runs.jsonl` — every cycle records, including skips.

## Tests

`tests/test_billing_gate.py` covers:

1. Missing stripe config ⇒ gate doesn't apply (allowed=True, gate_applies=False).
2. Missing catalog ⇒ allowed=True with "catalog not yet synced" reason.
3. Account with billing config behaves correctly in soft-mode vs hard-mode when the subscription is absent.
