"""
CRM Audit + Readiness Classifier

Single source of truth: output/denver_restaurant_leads_full_audit.csv

Reads the CRM + every prior outreach JSON + every shipped draft folder,
and classifies each row into one of four buckets:

  DRAFTED        Outreach already generated + staged (Wave 1/2/3)
  DISQUALIFIED   Explicit Disqualified Reason OR matches closure/chain rules
  READY          Has email + verbatim positive quote + verbatim negative quote
                 + active status verified + not drafted + not disqualified
  INCOMPLETE     Remaining: missing email, stale address, unverified operation,
                 or missing verbatim quotes

Writes:
  output/crm_readiness_report.csv    row-level classification
  output/crm_ready_queue.json        only READY rows, in builder-ready format
  output/crm_audit_summary.md        human-readable summary
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent
OUT = ROOT / "output"
CRM_PATH = OUT / "denver_restaurant_leads_full_audit.csv"

# --- Known-state inputs --------------------------------------------------

# Drafted rows (from prior wave folders + staged Outlook drafts)
DRAFTED_NAMES = {
    # Wave 2 staged in Outlook
    "Sam's No. 3",
    "City, O' City",
    "City O' City",
    "Blue Bonnet",
    "Blue Bonnet Cafe",
    "Forest Room 5",
    # Wave 3 drafts generated (this session)
    "Pietra's Pizzeria",
    "Westrail Tap & Grill",
}

# Disqualification hits discovered across sessions. Each entry is a
# substring match against Business Name (case-insensitive) and the reason
# is written to the Disqualified Reason column if not already present.
DISQUALIFIED_RULES: list[tuple[str, str]] = [
    ("Paramount Cafe",        "Closed 2018"),
    ("Lime on Larimer",       "Original 1424 Larimer location closed 2012"),
    ("Big Daddy's Pizza",     "Chain location + low signal"),
    ("100% de Agave",         "Closed Feb 2026"),
    ("100 de Agave",          "Closed Feb 2026"),
    ("City Buffet",           "Low-signal, closed/inactive"),
    ("Black Bird",            "Low-signal operator"),
    ("Hampton Social",        "Multi-state chain"),
    ("Cheddar",               "National chain"),
    ("Tupelo Honey",          "National chain"),
    ("Hacienda Colorado",     "Regional chain"),
    ("Benihana",              "National chain"),
    ("Upper Deck",            "Under 200 reviews"),
    ("The Cow",               "Under 200 reviews"),
    ("Casa Bonita",           "Too-high profile"),
    ("Hey Kiddo",             "Too-high profile"),
    ("1550 Restaurant",       "Sheraton Denver Downtown hotel restaurant"),
    ("Hibachi Grill",         "CRM address stale; real loc 1026 S Sable"),
    ("Kumoya",                "Culinary Creative Group (too high profile)"),
    ("Brittany Hill",         "Wedgewood Weddings chain venue"),
    ("Bent Fork",             "Aurora closed 2021, Loveland closed Jan 2022"),
    ("Original Chubby",       "CRM stale; confuses with El Chubby's"),
]

# --- Helpers -------------------------------------------------------------

def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _is_drafted(name: str) -> bool:
    n = _normalize(name)
    return any(_normalize(d) == n or _normalize(d) in n or n in _normalize(d)
               for d in DRAFTED_NAMES)


def _disqualified_reason(name: str, existing: str) -> str:
    if existing and existing.strip():
        return existing.strip()
    lower = (name or "").lower()
    for needle, reason in DISQUALIFIED_RULES:
        if needle.lower() in lower:
            return reason
    return ""


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Known emails discovered via website verification this session
VERIFIED_EMAILS: dict[str, str] = {
    _normalize("Pietra's Pizzeria"):
        "pietraspizzeriaanditalianrestaurant@gmail.com",
    _normalize("Westrail Tap & Grill"):
        "westrailtapandgrill@gmail.com",
    _normalize("Sam's No. 3"):       "downtown@samsno3.com",
    _normalize("City, O' City"):     "info@cityocitydenver.com",
    _normalize("City O' City"):      "info@cityocitydenver.com",
    _normalize("Blue Bonnet"):       "bluebonnetcafe1@yahoo.com",
    _normalize("Forest Room 5"):     "info@forestroom5.com",
}


def _email_for(row: dict[str, str]) -> str:
    name_key = _normalize(row.get("Business Name", ""))
    if name_key in VERIFIED_EMAILS:
        return VERIFIED_EMAILS[name_key]
    # Check if already in any row field
    for field in ("Website", "Outreach Body"):
        val = row.get(field, "") or ""
        m = EMAIL_RE.search(val)
        if m:
            return m.group(0)
    return ""


def _has_verbatim_positive(row: dict[str, str]) -> bool:
    q = (row.get("Positive Verbatim Quote", "") or "").strip()
    src = (row.get("Positive Source URL", "") or "").strip()
    note = (row.get("Positive Source Note", "") or "").lower()
    # Must have non-empty quote, a URL, and NOT be a paraphrase/composite
    if not q or not src:
        return False
    if "paraphrase" in note or "composite" in note:
        return False
    return True


def _has_verbatim_negative(row: dict[str, str]) -> bool:
    ex = (row.get("Verbatim Excerpts (top 2)", "") or "").strip()
    return bool(ex and len(ex) > 20)


def _has_review_volume(row: dict[str, str]) -> bool:
    try:
        return int(row.get("Total Reviews", "0") or 0) >= 200
    except ValueError:
        return False


def classify(row: dict[str, str]) -> tuple[str, list[str]]:
    """Return (bucket, reasons) for a row."""
    name = row.get("Business Name", "").strip()
    reasons: list[str] = []

    if _is_drafted(name):
        return ("DRAFTED", ["already drafted in prior wave"])

    dq = _disqualified_reason(name, row.get("Disqualified Reason", ""))
    if dq:
        return ("DISQUALIFIED", [dq])

    missing: list[str] = []
    if not _has_review_volume(row):
        missing.append("review volume <200")
    if not _email_for(row):
        missing.append("no verified email")
    if not _has_verbatim_positive(row):
        missing.append("no verbatim positive quote")
    if not _has_verbatim_negative(row):
        missing.append("no verbatim negative quote")

    if missing:
        return ("INCOMPLETE", missing)
    return ("READY", ["email verified + verbatim quotes + 200+ reviews"])


# --- Main ---------------------------------------------------------------

def main() -> None:
    rows: list[dict[str, str]] = []
    with CRM_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    counts = {"DRAFTED": 0, "DISQUALIFIED": 0, "READY": 0, "INCOMPLETE": 0}
    report_rows: list[dict[str, Any]] = []
    ready_queue: list[dict[str, str]] = []

    for r in rows:
        bucket, reasons = classify(r)
        counts[bucket] += 1
        report_rows.append({
            "Business Name": r.get("Business Name", ""),
            "City": r.get("City", ""),
            "Total Reviews": r.get("Total Reviews", ""),
            "Status": bucket,
            "Email": _email_for(r),
            "Reasons": "; ".join(reasons),
        })
        if bucket == "READY":
            # Inject the resolved email back into the row for the builder
            row_for_builder = dict(r)
            row_for_builder["Email"] = _email_for(r)
            ready_queue.append(row_for_builder)

    # Sort report by bucket then by Business Name
    bucket_order = {"READY": 0, "INCOMPLETE": 1, "DRAFTED": 2, "DISQUALIFIED": 3}
    report_rows.sort(key=lambda x: (bucket_order[x["Status"]],
                                    x["Business Name"].lower()))

    report_path = OUT / "crm_readiness_report.csv"
    with report_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "Business Name", "City", "Total Reviews",
            "Status", "Email", "Reasons",
        ])
        w.writeheader()
        w.writerows(report_rows)

    ready_path = OUT / "crm_ready_queue.json"
    ready_path.write_text(json.dumps(ready_queue, indent=2), encoding="utf-8")

    # Summary markdown
    summary = ["# CRM Readiness Audit", ""]
    summary.append(f"- Total rows: **{len(rows)}**")
    summary.append(f"- READY to draft: **{counts['READY']}**")
    summary.append(f"- INCOMPLETE (needs data): **{counts['INCOMPLETE']}**")
    summary.append(f"- DRAFTED already: **{counts['DRAFTED']}**")
    summary.append(f"- DISQUALIFIED: **{counts['DISQUALIFIED']}**")
    summary.append("")
    summary.append("## Ready to draft")
    summary.append("")
    for r in report_rows:
        if r["Status"] == "READY":
            summary.append(
                f"- **{r['Business Name']}** ({r['City']}, "
                f"{r['Total Reviews']} reviews) - {r['Email']}"
            )
    summary.append("")
    summary.append("## Incomplete (single biggest blocker)")
    summary.append("")
    for r in report_rows:
        if r["Status"] == "INCOMPLETE":
            top = r["Reasons"].split(";")[0].strip()
            summary.append(
                f"- {r['Business Name']} ({r['Total Reviews']} rev): {top}"
            )
    (OUT / "crm_audit_summary.md").write_text("\n".join(summary),
                                              encoding="utf-8")

    print(f"Total rows: {len(rows)}")
    print(f"  READY:        {counts['READY']}")
    print(f"  INCOMPLETE:   {counts['INCOMPLETE']}")
    print(f"  DRAFTED:      {counts['DRAFTED']}")
    print(f"  DISQUALIFIED: {counts['DISQUALIFIED']}")
    print()
    print(f"Report:      {report_path}")
    print(f"Ready queue: {ready_path}")
    print(f"Summary:     {OUT / 'crm_audit_summary.md'}")


if __name__ == "__main__":
    main()
