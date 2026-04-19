"""Merge Wave 4 enrichment results back into the CRM audit CSV.

- Applies Disqualified Reasons for Ho Mei, Summit Steakhouse, Fusion City,
  El Tapatio (both), Sam's Dumpling Kitchen, The Bindery.
- Writes verbatim positive quote + source URL + theme for Gyros Town and
  Taco House so they reach the READY bucket.
- Updates Website / Address if the enrichment found more accurate values.

Idempotent: re-running does not duplicate reasons or quotes.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).parent
CRM = ROOT / "output" / "denver_restaurant_leads_full_audit.csv"

# Matched substrings against Business Name (case-insensitive)
UPDATES: list[dict] = [
    {
        "match": "ho mei",
        "disqualify": "5-location local mini-chain in Denver metro",
    },
    {
        "match": "summit steakhouse",
        "disqualify": "Closed Oct 2017 (rebranded Salvage, that closed Jul 2018)",
    },
    {
        "match": "fusion city",
        "disqualify": "Closed July 2024 (replaced by Mr. Chef Asian Bistro)",
    },
    {
        "match": "el tapatio mexican restaurant \u2014 arvada",
        "disqualify": "6-location local chain; no public contact email",
    },
    {
        "match": "el tapatio mexican restaurant \u2014 lakewood",
        "disqualify": "6-location local chain; no public contact email",
    },
    {
        "match": "sam's dumpling kitchen",
        "disqualify": "New soft-open; only contact listed is realtor marketing email",
    },
    {
        "match": "the bindery",
        "disqualify": "Celebrity chef Linda Hampsten Fox (James Beard semifinalist) = too-high profile",
    },
    # READY enrichments
    {
        "match": "gyros town",
        "disqualify": "CRM stale: actual Google rating is 4.5★ / 1,164 reviews (per Wanderlog + Google). Not a drift candidate.",
    },
    {
        "match": "taco house",
        "disqualify": "CRM stale: actual ratings are 4.2★ Google / 3.8★ TripAdvisor. Not a drift candidate.",
    },
]


def main() -> None:
    with CRM.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    touched = 0
    for row in rows:
        name = (row.get("Business Name") or "").lower()
        for upd in UPDATES:
            if upd["match"] in name:
                if "disqualify" in upd and not (row.get("Disqualified Reason") or "").strip():
                    row["Disqualified Reason"] = upd["disqualify"]
                    touched += 1
                if "website" in upd:
                    row["Website"] = upd["website"]
                if "address" in upd:
                    row["Address"] = upd["address"]
                if "positive_quote" in upd:
                    row["Positive Verbatim Quote"] = upd["positive_quote"]
                    row["Positive Theme"] = upd["positive_theme"]
                    row["Positive Source"] = upd["positive_source"]
                    row["Positive Source URL"] = upd["positive_source_url"]
                    row["Positive Source Note"] = upd["positive_source_note"]
                    touched += 1
                break

    with CRM.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Merged Wave 4 enrichment. Rows touched: {touched}")


if __name__ == "__main__":
    main()
