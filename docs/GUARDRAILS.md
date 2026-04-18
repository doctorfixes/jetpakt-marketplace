# Safety & Legal Guardrails

These rules are baked into `pipeline.py` and must stay in place in any fork
or derivative. They exist because the ReviewSentinel™ Denver pilot operates
in a market with **active service-fee litigation**
([Culinary Creative Group lawsuit, April 2025](https://localnews8.com/cnn-regional/2025/04/02/denver-restaurant-group-faces-lawsuit-from-former-employees-over-20-service-charge-misuse/))
and high scrutiny on hospitality labor practices.

## 1. No individuals — ever

- Do **not** name servers, hosts, managers, or owners in any outreach copy.
- Do **not** quote reviews that name an individual, even if the review is public.
- If the verbatim quote mentions a person by name, redact to "a staff member"
  or skip that excerpt.

## 2. Verbatim-only quoting

- Every review excerpt stored in `verbatim_review_excerpts` must be a
  direct quote from a public-facing review (Google, Yelp, Tripadvisor,
  Reddit, Indeed).
- No paraphrasing. No "AI-synthesized" quotes. No invented details.
- Source URL must be captured in the seed JSON for every restaurant so
  any quote can be traced back.

## 3. Defamation-safe outreach copy

Outreach body **must**:

- Reference complaint *categories* (e.g. "billing transparency") not
  specific allegations.
- Avoid quoting reviews that contain illness claims, racial complaints,
  sexual-harassment allegations, or wage-theft allegations.
- Never imply the restaurant is actually guilty of anything — only that
  guests are *expressing concerns*.
- Position the sender as offering to help close the loop, not as
  auditing/policing the business.

## 4. Legal-review flags (mandatory human gate)

The pipeline auto-flags two complaint buckets for human legal review
before any outreach goes out:

| Bucket | Flag | Why |
|---|---|---|
| `billing / service-fee transparency` | HIGH | Wage/service-fee disclosure. Denver CCG lawsuit is active; any outreach that references 15-22% service charges needs counsel review. |
| `food safety perception` | MEDIUM | Alleges illness. Quoting specific illness claims risks defamation. Drop specific illness language from outreach. |

Leads with these flags should have their `Outreach Body` reviewed by a
human (and ideally legal counsel) before send. The `Sent Status` column
defaults to `NOT_SENT — awaiting human review` to enforce this.

## 5. Human-in-the-loop send gate

The pipeline writes **drafts**, not sends.

- `Sent Status` column starts at `NOT_SENT — awaiting human review` for
  every lead.
- Automation tools (Zapier, Make, HubSpot sequences) must be configured
  to require a human click-approve step before changing `Sent Status` to
  `SENT <date>`.
- Never wire the CSV directly into an auto-send queue without that gate.

## 6. Data sourcing

- Only public review data — no scraping behind authentication.
- No employee data, no Indeed reviews quoted in outreach copy
  (employer-reviews are off-limits for customer outreach because they
  surface wage/culture claims).
- When Google Places API is connected, use only the public endpoints —
  do not attempt to pull reviews that require elevated authorization.

## 7. Record-keeping

For every lead that is actually contacted:

- Log the date, the exact outreach body sent, and the human reviewer's
  initials.
- Retain source-URL list for each referenced complaint.
- If the restaurant responds asking how you obtained their review data,
  you must be able to show the public source URLs.

## 8. Opt-out handling

- If a restaurant asks to be removed from outreach, add them to an
  `excluded_businesses.json` file and honor it permanently.
- Do **not** re-solicit after 30 days "just in case."

## 9. Credit / attribution

When pitching, be ready to share:

- The public source URLs behind each claim.
- The scoring methodology.
- A sample redacted Experience Enhancement Guide (see the ReviewSentinel
  pilot deliverables for Casa Bonita, Hampton Social, Hey Kiddo).

## 10. What NOT to do

- ❌ Don't send cold outreach referencing specific 1-star reviews by URL.
- ❌ Don't quote a review that names a staff member.
- ❌ Don't quote Indeed employee reviews in customer outreach.
- ❌ Don't auto-send without a human review gate.
- ❌ Don't use complaint signals drawn from a single review — require at
  least 3 reviews touching the same theme before flagging a bucket.
- ❌ Don't promise to "remove" or "bury" negative reviews. That's against
  Google's policies and invites legal exposure. Position as "close the
  loop" not "clean the page."
