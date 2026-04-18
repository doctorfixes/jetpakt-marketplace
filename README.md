# Denver Restaurant Reputation-Management Lead Pipeline

A runnable Python pipeline that identifies non-chain Denver restaurants with
frequent, recent negative Google/Yelp reviews and generates CRM-ready leads
with personalized outreach drafts.

Built as an extension of the ReviewSentinel™ Denver pilot — same
safety-first architecture (no individuals named, verbatim-only quoting,
human-approval before send, legal-review flags on wage/service-fee items).

## What it does

1. **Sources candidates** — 26 hand-verified Denver restaurants drawn from
   Google Maps public pages, Yelp's "Worst Restaurant Near Denver" search,
   r/denverfood threads, Tripadvisor, and Westword/local-news coverage.
2. **Scores complaint signals** — keyword classifier across 8 buckets
   (service, food quality, cleanliness, billing, perceived value, host
   experience, server attitude, food safety).
3. **Filters for qualified leads** — excludes chains, restaurants already
   responding to negative reviews, low-volume review counts, and ratings
   above the 3.5-star ceiling.
4. **Generates outreach** — populates a direct reputation-management
   subject + body, references the top complaint bucket, applies
   defamation-safe guardrails (nothing invented, no staff named, no
   specific illness claims quoted).
5. **Exports CRM-ready CSV** — ready to import into HubSpot, Salesforce,
   or any spreadsheet.

## Run it

```bash
cd denver_leadgen

# Full pipeline — writes CSVs to output/
python pipeline.py --run

# Preview top 10 leads without writing
python pipeline.py --preview

# Just list candidate counts
python pipeline.py --fetch-only
```

## Output

Two CSVs land in `output/`:

- **`denver_restaurant_leads.csv`** — qualified leads only, sorted by
  complaint score. Ready for CRM import.
- **`denver_restaurant_leads_full_audit.csv`** — every candidate including
  disqualified ones, with a `Disqualified Reason` column explaining why.
  Use this to sanity-check the filter logic.

### CSV columns

| Column | Description |
|---|---|
| Business Name | Restaurant name |
| Category | Cuisine / type |
| Neighborhood | Denver-metro area |
| Address | Street address |
| Phone | Main line |
| Website | Official website (nullable) |
| Google Review Link | Direct link to Google Maps reviews |
| Rating | Current Google rating |
| Total Reviews | Volume — must be >= 200 to qualify |
| Recent Negative Share (30d) | % of reviews in last 30d that are negative |
| Key Complaint | Top complaint bucket (e.g. "billing / service-fee transparency") |
| Complaint Score (0-100) | Weighted composite: rating gap + neg share + review volume |
| Legal Review Flag | Populated for wage/service-fee/food-safety-related leads |
| Verbatim Excerpts (top 2) | Real review quotes, `||`-separated |
| Outreach Subject | Drafted subject line |
| Outreach Body | Drafted email body |
| Sent Status | Defaults to `NOT_SENT — awaiting human review` |
| Disqualified Reason | Populated in audit CSV if filtered out |

## Configuration

Tune thresholds in `pipeline.py` (top-of-file constants):

```python
RATING_CEILING = 3.5             # Only flag restaurants at/below this rating
MIN_REVIEW_COUNT = 200           # Need enough volume to be worth outreach
MIN_RECENT_NEGATIVE_SHARE = 0.20 # >=20% of recent reviews must be negative
EXCLUDE_CHAINS = True
EXCLUDE_ALREADY_RESPONDING = True
```

Add/remove complaint keywords in `COMPLAINT_BUCKETS`.
Add/remove chains in `CHAIN_NAMES`.
Edit outreach copy in `OUTREACH_SUBJECT_TEMPLATES` and `OUTREACH_BODY_TEMPLATE`.

## Scaling to live data

The current pipeline ships with a hand-verified seed list of 26 real Denver
restaurants so it's runnable out of the box with zero API keys. Three paths
to go live:

1. **Google Maps Places API** — connect the `google_maps_platform`
   connector. Replace `fetch_candidates_from_google_maps()` with a call
   to the Places API `nearbysearch` endpoint, paginated across Denver
   neighborhoods. Free tier gives ~10k requests/month.

2. **Apollo.io enrichment** — connect the `apollo_io` connector to append
   owner/GM names and verified emails. Pipe the `Business Name` + `Address`
   through Apollo's company search, take the top result, then pull
   contacts with titles matching `owner|gm|manager`.

3. **Outreach automation** — wire the CSV output into HubSpot sequences
   or Apollo sequences. **Keep the human-approval step** — don't auto-send.
   Mark `Sent Status` = "SENT <date>" only after a human clicks approve.

## Safety & legal guardrails

See `docs/GUARDRAILS.md` for the full list. Short version:

- ✅ Only verbatim public quotes — no paraphrasing, no invention
- ✅ No individual staff names in outreach copy
- ✅ No specific illness/food-poisoning claims quoted in outreach
- ✅ Wage/service-fee complaints get a `Legal Review Flag` — require
  human legal review before send given the Denver Culinary Creative
  Group service-fee lawsuit context
- ✅ Outreach is DRAFTED, not auto-sent. `Sent Status` defaults to
  `NOT_SENT — awaiting human review`
- ✅ Review data is from public sources only; no scraping behind auth,
  no employee/private data

## Project layout

```
denver_leadgen/
├── pipeline.py                 # Main pipeline (5 stages)
├── README.md                   # This file
├── data/
│   └── seed_candidates.json    # Hand-verified seed list (26 restaurants)
├── output/
│   ├── denver_restaurant_leads.csv           # Qualified leads (CRM-ready)
│   └── denver_restaurant_leads_full_audit.csv # All candidates with reasons
└── docs/
    ├── GUARDRAILS.md           # Full defamation/legal guardrails
    └── OUTREACH_TEMPLATES.md   # All email templates + variations
```
