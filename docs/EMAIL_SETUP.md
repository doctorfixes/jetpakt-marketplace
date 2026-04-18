# Email Setup — gojetpakt.us@outlook.com

## TL;DR

The Outlook connector is authenticated. Sends go out directly from
`gojetpakt.us@outlook.com` via Microsoft Graph. No SMTP passwords,
no ESP verification, no relay. The agent drives each send with a
human-in-the-loop confirmation.

---

## Path A — Outlook connector (default, recommended)

### Why it's the best option for this project
- **Native Microsoft sending.** Messages originate from your real
  mailbox, so deliverability matches any email you send from Outlook
  manually.
- **No credentials in code.** Authorization is OAuth through the
  Perplexity connector — no app password, no SMTP string.
- **Replies land in your inbox.** Restaurants replying to the pitch
  thread appear in your normal Outlook inbox and are searchable.
- **Free-tier limit ≈ 300 messages/day.** Plenty of headroom for 30
  qualified leads + follow-ups.

### How a send round works inside the agent
1. You ask the agent to send outreach to N leads (optionally filtered
   by city, by top-score rank, or by a manual pick list).
2. Agent re-runs the dry-run preview against the CRM CSV.
3. Agent **automatically skips** any row with a `Legal Review Flag`
   set.
4. For each remaining row, agent shows you the exact subject + body
   + recipient and asks for per-send approval (or a single
   `--yes-all`-style batch approval for a bounded list).
5. Approved rows are sent through `outlook.send_email`. The agent
   records the message id in the CSV `Sent Status` column.

### How to run mailer.py locally alongside the connector
`mailer.py` defaults to `MAIL_PROVIDER=outlook`. In that mode it
does **not** send directly — it appends each intended send to
`output/outlook_send_queue.jsonl`. You then ask the agent to drain
the queue, which walks the file and calls `outlook.send_email` for
each row (still with per-row confirmation). This gives you the same
safety loop whether you launch sends from the CLI or from chat.

---

## Path B — SMTP direct (fallback)

Use this only if the Outlook connector is unavailable (e.g. you
revoked the OAuth token or are running the script off-platform).

```bash
export MAIL_PROVIDER="smtp"
export MAIL_FROM="gojetpakt.us@outlook.com"
export MAIL_SMTP_HOST="smtp.office365.com"
export MAIL_SMTP_PORT="587"
export MAIL_SMTP_USER="gojetpakt.us@outlook.com"
export MAIL_SMTP_PASS="<app-password from account.microsoft.com>"

python mailer.py --csv output/denver_restaurant_leads.csv --send --limit 5
```

Notes:
- Outlook requires an **app password** for SMTP — your normal login
  password will be rejected if 2FA is on (which it should be).
  Generate one at `account.microsoft.com/security` → App passwords.
- Outlook throttles around ~300 recipients/day and ~30/minute on the
  free tier. Respect the 2-second throttle that's already baked into
  `mailer.py`.

---

## Path C — ESP relay (scale only)

Only needed if you grow past ~300/day or want tracking/warmup.
SendGrid, Mailgun, Postmark, Amazon SES, and Instantly adapters are
wired into `mailer.py`. Each requires:
1. Connecting the ESP via the Perplexity integrations tab.
2. Verifying `gojetpakt.us@outlook.com` as a sending identity
   inside the ESP (one-click email verification).

This is deliberately out-of-scope until volume demands it.

---

## Enrichment — filling the `Email` column

`mailer.py` skips any row with a blank `Email` cell. The 30 qualified
leads ship with empty email cells by default. Options:

- **Apollo.io connector** — recommended. After authentication, the
  agent runs owner/manager lookups for every restaurant and populates
  the CRM CSV in place.
- **Hunter.io connector** — alternative email-finder. Good for
  small-business domains where Apollo coverage is thin.
- **Manual** — open the CSV and paste in the `info@` or `contact@`
  address from each restaurant's website. Slower, zero cost.

---

## Guardrails that are always enforced

Independent of which path you pick:

1. **Dry-run by default.** No `--send` flag means nothing leaves the
   sandbox.
2. **Legal flag auto-skip.** Any row with `Legal Review Flag` set
   (service-fee transparency or food-safety complaint buckets) is
   blocked from automated sending.
3. **Per-row confirmation.** Each send requires a `y` unless the
   caller passes `--yes-all` for a bounded batch.
4. **No individuals named.** Outreach copy references verbatim public
   reviews and the business only — never a named manager, owner, or
   staff member.
5. **Sent Status is the source of truth.** No row is marked sent until
   the connector returns success.
