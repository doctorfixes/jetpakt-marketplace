# JetPakt hourly Stripe poll — cron task

**Schedule:** `0 * * * *` UTC (hourly, top of the hour)
**Background:** true
**Exact:** false (OK for minute to vary; jitter spreads load)

## Purpose

Close the loop on Phase 1: automatically onboard any paying Stripe customer
whose subscription is not yet tracked on the Clients tab. Runs every hour,
does nothing on quiet hours, notifies only when a new client is onboarded
and needs Ryan's welcome-draft approval.

## Why hourly, not every 15 minutes

A new signup waiting up to 60 minutes for their welcome draft is invisible
to them (the email still reads "your subscription is active; first memo
by ...") and saves ~3x the credits vs. a 15-minute cadence. Upgrade to
15-min only when signup volume justifies it.

## Idempotency guarantee

`client_id = "client_" + sha1(customer_id + product_id)[:8]`. The cron
computes this for every Stripe subscription found, reads the Clients tab,
and only onboards new client_ids. Rerunning on a quiet hour is a pure
read and does not write anything.

## Task description (paste into schedule_cron)

---

You are running the JetPakt hourly Stripe poll. Your job is to find any
paying Stripe subscriptions (or recent Scan one-time purchases) that are
not yet tracked on the Clients tab, and onboard each one via
`./jetpakt onboard`. Silent on quiet hours — only notify when a new
client is onboarded.

Use the `stripe` connector and the `google_sheets__pipedream` connector.
Never use browser_task for Sheets or Stripe — the connectors are the path.

### Config

- Sheet ID: `1L2NqIcZeG_SMqoL_L3YN_IlqiVkMWy4SyBsu2Sa07yI`
- Clients tab: `sheetName="Clients"`, worksheetId=`534094040`
- Prospects tab: `sheetName="Prospects"`, worksheetId=`2139708364`
- Working dir: `/home/user/workspace/cron_tracking/{cron_id}/`

### Steps

1. **List active + trialing subscriptions.** Call `stripe.list_subscriptions`
   with `status="active"` and `limit=100`. Then call it again with
   `status="trialing"` and `limit=100`. Merge. For each subscription,
   extract: `id`, `customer` (= customer_id), the first item's
   `price.id` and `price.product` (= product_id), and `status`.

2. **Also scan recent one-time Scan purchases.** Call
   `stripe.list_payment_intents` with `limit=50`. Filter to
   `status="succeeded"` and those where the product is
   `prod_UMDaHMYdnHdW2H` (Scan). These do NOT create subscriptions —
   they still need onboarding as a one-time Scan.
   For each successful Scan payment, synthesize a pseudo-subscription
   object with `id=pi_<payment_intent_id>`, the customer_id, and
   `product_id=prod_UMDaHMYdnHdW2H`. Only include ones from the last
   48 hours (check `created` timestamp).

3. **Compute the set of expected client_ids.** For each subscription (real
   or synthesized), compute
   `client_id = "client_" + sha1(f"{customer_id}::{product_id}".encode()).hexdigest()[:8]`.

4. **Read the Clients tab.** Call `google_sheets-read-rows` with
   `sheetName="Clients"`, `hasHeaders=true`. Collect the set of existing
   `client_id` values in column A.

5. **Diff.** `to_onboard = expected_client_ids - existing_client_ids`. If
   empty, end silently (no notification).

6. **For each to_onboard client_id:**

   a. Find the matching subscription object from step 1-2.
   b. Call `stripe.fetch_stripe_resources` (or `list_customers` with
      `email` filter if no fetch by id works) to get the customer's
      `id, email, name, phone`.
   c. Write `/home/user/workspace/cron_tracking/{cron_id}/<client_id>/stripe_customer.json`
      with that customer data.
   d. If this is a real subscription (not a synthesized Scan payment),
      write `stripe_subscription.json` with
      `{id, customer_id, product_id, price_id, status, current_period_start, current_period_end}`.
      For synthesized Scan payments, do NOT write subscription.json
      (onboard handles Scan when --subscription is omitted).
   e. Read the Prospects tab: `google_sheets-read-rows` with
      `sheetName="Prospects"`, `hasHeaders=true`. Filter to rows with
      non-empty `owner_email`. Write the list as a JSON list of
      `{prospect_id, business_name, owner_email, stage, legal_severity}`
      (rename `legal_flag_severity` to `legal_severity`) to
      `prospects.json` in the working dir.
   f. Run:
      ```
      cd /home/user/workspace/denver_leadgen && ./jetpakt onboard \
        --customer    /home/user/workspace/cron_tracking/{cron_id}/<client_id>/stripe_customer.json \
        --subscription /home/user/workspace/cron_tracking/{cron_id}/<client_id>/stripe_subscription.json \
        --prospects   /home/user/workspace/cron_tracking/{cron_id}/prospects.json \
        --out         /home/user/workspace/cron_tracking/{cron_id}/<client_id>/onboarding_plan.json
      ```
      (Omit --subscription flag for synthesized Scan.)

   g. Apply the plan against the Sheet:
      - `clients_append`: call `google_sheets-add-multiple-rows`
        `sheetName="Clients"`, `rows = json.dumps([positional_row])`
        (18 cells).
      - `prospect_updates`: for each, call `google_sheets-find-row`
        with `sheetName="Prospects"`, `column="A"`, `value=prospect_id`
        to get row N. Read A{N}:Z{N} with `hasHeaders=false`. Mutate:
        index 20 (col U, stage), index 21 (col V, stage_entered_at),
        index 23 (col X, notes: existing + "; " + notes_append;
        skip "; " if blank), index 25 (col Z, updated_at). NEVER
        overwrite a row where current stage is "Disqualified" — skip
        instead. Write back with
        `google_sheets-update-multiple-rows` `range=f"A{N}:Z{N}"`,
        `rows=json.dumps([updated_26_cells])`.

   h. Apply the Outlook welcome draft:
      - For each item in `outlook_drafts`, call `outlook.draft_email`
        with `to`, `cc=[]`, `bcc=[]`, `subject`, `body`. DO NOT send.

7. **Notify.** After all onboardings, call `send_notification`:
   - `title`: `f"JetPakt: {N} new client(s) awaiting welcome approval"`
   - `body`: one line per onboarded client:
     `f"{tier} ${mrr}/mo — {business_name} ({contact_email}) — first memo due {next_deliverable_due}"`.
     Include `"Review drafts in Outlook Drafts folder."` and a link to
     the Sheet: `https://docs.google.com/spreadsheets/d/1L2NqIcZeG_SMqoL_L3YN_IlqiVkMWy4SyBsu2Sa07yI/edit`.
   - `schedule_description`: `"Hourly"`
   - `url`: the Sheet URL.

### Failure handling

- If any connector returns `requires_auth=true` or an auth error, write a
  one-line entry to `/home/user/workspace/cron_tracking/{cron_id}/failure.log`
  and end. DO NOT retry the same call repeatedly.
- If `jetpakt onboard` returns a non-zero exit code (e.g., unknown
  `product_id`), log to `failure.log`, notify Ryan with
  `title="JetPakt: onboard CLI failed for <customer_id>"` and continue
  with remaining clients. One bad record must not block the others.
- If the Clients tab read returns an empty header row (new, no data
  yet), treat existing_client_ids as empty set (don't error).

### Files produced per run

Under `/home/user/workspace/cron_tracking/{cron_id}/`:

- `prospects.json` — Prospects snapshot for matching
- `<client_id>/stripe_customer.json` — per onboarded client
- `<client_id>/stripe_subscription.json` — per onboarded client (subscription only)
- `<client_id>/onboarding_plan.json` — the authoritative audit record
- `failure.log` — only on error

### Constraints

- NEVER send emails, only draft.
- NEVER modify Stripe (read-only).
- NEVER write to Prospects rows at stage `Disqualified`.
- The CLI call is the only place that generates the welcome copy —
  do not author your own welcome email inline.
