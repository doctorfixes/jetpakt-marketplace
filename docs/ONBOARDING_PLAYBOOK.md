# JetPakt onboarding playbook

The moment a prospect becomes a paying Stripe customer, this playbook runs.
Goal: first deliverable in their inbox within the SLA window with zero
manual data entry.

## SLA by tier

| Tier | Stripe product | Cadence | First memo due | Follow-on cadence |
|---|---|---|---|---|
| Scan | `prod_UMDaHMYdnHdW2H` | One-time | within 2 business days | n/a |
| Pulse Essentials ($149/mo) | `prod_UMDbLrW0doOHPI` | Monthly | day 30 | 1st of each month |
| Pulse Pro ($399/mo) | `prod_UMDcmqaEyH1UBd` | Weekly | day 7 | every Monday 9am MDT |
| Pulse Alert ($899/mo) | `prod_UMDdOzoVVKTCZj` | Weekly + crisis | day 7 | every Monday + same-day HIGH alerts |
| Pulse Concierge ($1,499/mo) | `prod_UMDebs2GG5zR4B` | Weekly + on-call | day 7 | every Monday + on-demand |

## Pipeline (from signup to first memo)

```
Stripe event                     Ryan review             Cron
─────────────                    ────────────            ────
1. checkout.session.completed
       │
2. jetpakt onboard
   ├─ Clients row appended
   ├─ Prospects stage → Client
   └─ Welcome draft staged in Outlook
       │
3. Ryan opens Drafts folder      ◄── per-row approval
       │                              drafts-over-auto-send rule
4. Ryan clicks Send
       │
5. Client receives welcome
       │
6. next_deliverable_due fires                            ◄── daily cron
       │
7. jetpakt pulse generates first memo (Phase 2)
```

## jetpakt onboard (CLI)

```bash
jetpakt onboard \
  --customer    /path/to/stripe_customer.json \
  --subscription /path/to/stripe_subscription.json  # omit for Scan
  --prospects   /path/to/prospects.json \
  --out         /path/to/onboarding_plan.json
```

**Inputs expected (normalize from Stripe API before passing in):**

`stripe_customer.json`:
```json
{"id": "cus_XXX", "email": "owner@restaurant.com", "name": "Owner Name", "phone": ""}
```

`stripe_subscription.json` (omit for Scan):
```json
{
  "id": "sub_XXX",
  "customer_id": "cus_XXX",
  "product_id": "prod_UMDbLrW0doOHPI",
  "price_id": "price_1TNVAPEa6thiGvoJjjyZQvGz",
  "status": "active",
  "current_period_start": "2026-04-19T00:00:00Z",
  "current_period_end":   "2026-05-19T00:00:00Z"
}
```

**Output** (`onboarding_plan.json`): `clients_append`, `prospect_updates`,
`outlook_drafts`, `summary`.

## How the agent applies the plan

1. **`clients_append`** → `google_sheets-add-multiple-rows`
   - `sheetName="Clients"`, `rows = json.dumps([positional_row])` (18 cells).

2. **`prospect_updates`** → find row by `prospect_id`, read A{N}:Z{N} with
   `hasHeaders=false`, mutate stage/notes/updated_at, write back via
   `google_sheets-update-multiple-rows`. Never override `Disqualified`.

3. **`outlook_drafts`** → one `outlook.draft_email` per draft. The welcome
   email uses the canonical signature and CAN-SPAM postal. Ryan reviews in
   Drafts and sends manually.

## Idempotency

- `client_id = "client_" + sha1(customer_id + product_id)[:8]` — running
  `jetpakt onboard` twice produces the same client_id. Dedupe on the
  Clients tab by checking `client_id` before appending.
- Welcome email `idempotency_key = welcome::<client_id>::<subject_hash8>`.

## Failure modes and what we do

| Failure | Behavior |
|---|---|
| Customer email does not match any prospect | Still onboards. `prospect_id` is synthesized `direct_<domain>_<name>`. No Prospects update (there is nothing to update). |
| Product_id not in `STRIPE_PRODUCT_TIER` | CLI exits non-zero with "Add to config.STRIPE_PRODUCT_TIER before onboarding." — new SKU requires a deliberate config change. |
| Prospect already at `Disqualified` stage | Onboarding proceeds (customer paid — we honor) but Prospects row is NOT flipped. A note is added via client row. |
| Welcome subject >45 chars | Falls back to `"<Tier> is active"`. |

## First-memo cron (Phase 2 — coming next)

A daily cron will:
1. Read Clients tab, filter `status=Active OR Trialing` and
   `next_deliverable_due <= today`.
2. For each: regenerate the drift memo (Scan one-off; Pulse diffs against
   last memo).
3. Draft delivery email in Outlook with `[DRAFT-JETPAKT]` prefix.
4. Notify Ryan with the list of drafts awaiting approval.
5. On send, update `last_memo_sent_at` + advance `next_deliverable_due`.

Not built yet. Tracked in `PHASE2_TODO.md`.
