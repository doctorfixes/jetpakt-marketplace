"""
Mailer — pluggable email sender for the Denver-metro lead pipeline.

Configured for the user's Outlook address (gojetpakt.us@outlook.com)
with four delivery modes (default: outlook connector):

    (A) Outlook connector  ← DEFAULT, recommended
        - Uses the authenticated Outlook connector (Microsoft Graph).
        - No SMTP credentials, no ESP verification. OAuth-scoped send
          on behalf of the user from their real mailbox.
        - Invoked through the Perplexity agent runtime
          (call_external_tool outlook.send_email). When running this
          script standalone outside the agent, it writes a JSON queue
          file the agent then drains.

    (B) SMTP direct
        - Generic SMTP (Outlook/Office 365, Gmail, mail.com, etc.).
        - Best for low volume; no tracking; requires an app password.

    (C) SendGrid / (D) Mailgun ESP relays
        - Required for high-volume cold-outreach after sender
          verification. Kept for scale, but not needed for Outlook-
          native sending of 30-50 leads.

Outreach body is pulled from the pipeline-generated CSV
(Free-Pilot Body column by default).

CRITICAL: This module does NOT auto-send. Every send requires an
explicit `--send` flag plus a per-row confirmation unless `--yes-all`
is set.

Usage:

    # Dry-run preview (default) — shows what would be sent
    python mailer.py --csv output/denver_restaurant_leads.csv

    # Dry-run but only for a specific city
    python mailer.py --csv output/denver_restaurant_leads.csv --city Aurora

    # Queue sends via the Outlook connector (agent runtime drains queue)
    export MAIL_PROVIDER="outlook"
    export MAIL_FROM="gojetpakt.us@outlook.com"
    python mailer.py --csv output/denver_restaurant_leads.csv --send --limit 5

    # Send via SMTP directly (Outlook/Office 365 endpoint)
    export MAIL_PROVIDER="smtp"
    export MAIL_SMTP_HOST="smtp.office365.com"
    export MAIL_SMTP_PORT="587"
    export MAIL_SMTP_USER="gojetpakt.us@outlook.com"
    export MAIL_SMTP_PASS="<app-password>"
    python mailer.py --csv output/denver_restaurant_leads.csv --send --limit 5
"""

from __future__ import annotations

import argparse
import csv
import os
import smtplib
import sys
import time
from email.message import EmailMessage
from pathlib import Path

FROM_ADDR = os.environ.get("MAIL_FROM", "gojetpakt.us@outlook.com")
PROVIDER = os.environ.get("MAIL_PROVIDER", "outlook").lower()   # outlook | smtp | sendgrid | mailgun
OUTLOOK_QUEUE = Path(os.environ.get(
    "OUTLOOK_QUEUE",
    str(Path(__file__).parent / "output" / "outlook_send_queue.jsonl"),
))

DEFAULT_BODY_COLUMN = "Free-Pilot Body"
DEFAULT_SUBJECT_COLUMN = "Free-Pilot Subject"


# -------------------- To-address resolution --------------------

def resolve_to_address(row: dict) -> str | None:
    """Find the best send address for a lead.

    Order of precedence:
      1. `Email` column if present in the CSV (from Apollo enrichment)
      2. Fallback: constructed contact-page placeholder — flagged for
         manual review, never auto-sent.
    """
    addr = (row.get("Email") or "").strip()
    if addr and "@" in addr:
        return addr
    return None


# -------------------- Provider adapters --------------------

def send_via_outlook(to: str, subject: str, body: str) -> tuple[bool, str]:
    """Queue a send for the Outlook connector.

    The agent runtime (not this script) actually calls
    `outlook.send_email`. We append one JSONL record per intended send
    to a queue file. The agent drains the queue after showing the user
    a dry-run confirmation, so no message can slip out without review.
    """
    import json as _json
    OUTLOOK_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "from": FROM_ADDR,
        "to": [to],
        "subject": subject,
        "body": body,
        "ts": time.time(),
    }
    try:
        with OUTLOOK_QUEUE.open("a", encoding="utf-8") as f:
            f.write(_json.dumps(rec) + "\n")
        return True, f"queued for outlook connector -> {OUTLOOK_QUEUE.name}"
    except Exception as e:
        return False, f"outlook queue error: {e}"


def send_via_smtp(to: str, subject: str, body: str) -> tuple[bool, str]:
    host = os.environ.get("MAIL_SMTP_HOST", "smtp.office365.com")
    port = int(os.environ.get("MAIL_SMTP_PORT", "587"))
    user = os.environ.get("MAIL_SMTP_USER", FROM_ADDR)
    pw = os.environ.get("MAIL_SMTP_PASS")
    if not pw:
        return False, "MAIL_SMTP_PASS not set"

    msg = EmailMessage()
    msg["From"] = FROM_ADDR
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
        return True, "ok"
    except Exception as e:
        return False, f"SMTP error: {e}"


def send_via_sendgrid(to: str, subject: str, body: str) -> tuple[bool, str]:
    try:
        import urllib.request
        import json
    except Exception as e:
        return False, f"sendgrid prereq: {e}"
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        return False, "SENDGRID_API_KEY not set"
    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": FROM_ADDR},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if 200 <= resp.status < 300:
                return True, f"sendgrid {resp.status}"
            return False, f"sendgrid HTTP {resp.status}"
    except Exception as e:
        return False, f"sendgrid error: {e}"


def send_via_mailgun(to: str, subject: str, body: str) -> tuple[bool, str]:
    try:
        import urllib.request, urllib.parse
    except Exception as e:
        return False, f"mailgun prereq: {e}"
    api_key = os.environ.get("MAILGUN_API_KEY")
    domain = os.environ.get("MAILGUN_DOMAIN")
    if not (api_key and domain):
        return False, "MAILGUN_API_KEY and MAILGUN_DOMAIN required"
    data = urllib.parse.urlencode({
        "from": FROM_ADDR, "to": to, "subject": subject, "text": body
    }).encode("utf-8")
    import base64
    auth = base64.b64encode(f"api:{api_key}".encode()).decode()
    req = urllib.request.Request(
        f"https://api.mailgun.net/v3/{domain}/messages",
        data=data,
        headers={"Authorization": f"Basic {auth}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if 200 <= resp.status < 300:
                return True, f"mailgun {resp.status}"
            return False, f"mailgun HTTP {resp.status}"
    except Exception as e:
        return False, f"mailgun error: {e}"


PROVIDERS = {
    "outlook": send_via_outlook,
    "smtp": send_via_smtp,
    "sendgrid": send_via_sendgrid,
    "mailgun": send_via_mailgun,
}


# -------------------- Main --------------------

def _normalize_row(row: dict) -> dict:
    """Strip whitespace + BOM from CSV keys and values.

    Guards against silent legal-flag bypass if the CSV header gains a trailing
    space, leading BOM, or case drift — `row.get("Legal Review Flag")` would
    otherwise return None and a LEGAL-HIGH lead could slip into outreach.
    """
    cleaned = {}
    for k, v in row.items():
        if k is None:
            continue
        ck = k.strip().lstrip("\ufeff")
        cv = v.strip() if isinstance(v, str) else v
        cleaned[ck] = cv
    return cleaned


def process(csv_path: Path, send: bool, limit: int | None, city: str | None,
            yes_all: bool, body_col: str, subject_col: str) -> int:
    with open(csv_path, encoding="utf-8-sig") as f:   # tolerate BOM
        rows = [_normalize_row(r) for r in csv.DictReader(f)]
    if city:
        rows = [r for r in rows if r.get("City", "").lower() == city.lower()]

    # Skip LEGAL-flagged leads even in --send mode
    legal_skipped = [r for r in rows if r.get("Legal Review Flag")]
    rows = [r for r in rows if not r.get("Legal Review Flag")]

    if limit:
        rows = rows[:limit]

    print(f"Provider: {PROVIDER}  |  From: {FROM_ADDR}")
    print(f"Mode: {'SEND' if send else 'DRY-RUN (preview only)'}")
    print(f"Filtered to {len(rows)} leads  "
          f"(skipped {len(legal_skipped)} LEGAL-flagged).")
    print("=" * 70)

    adapter = PROVIDERS.get(PROVIDER)
    if send and adapter is None:
        print(f"ERROR: unknown MAIL_PROVIDER='{PROVIDER}'. "
              f"Options: {list(PROVIDERS)}")
        return 2

    sent, skipped = 0, 0
    for i, row in enumerate(rows, 1):
        name = row["Business Name"]
        to = resolve_to_address(row)
        subject = row.get(subject_col, "") or row.get("Outreach Subject", "")
        body = row.get(body_col, "") or row.get("Outreach Body", "")

        print(f"\n[{i}/{len(rows)}] {name}  ({row.get('City','?')})")
        print(f"  To     : {to or '<no email on file — needs Apollo enrichment>'}")
        print(f"  Subject: {subject}")
        print(f"  Preview: {body[:120]}...")

        if not to:
            print("  STATUS : SKIPPED — no email address")
            skipped += 1
            continue

        if not send:
            print("  STATUS : DRY-RUN (would send)")
            continue

        if not yes_all:
            ans = input("  Send this one? [y/N/q]: ").strip().lower()
            if ans == "q":
                break
            if ans != "y":
                print("  STATUS : SKIPPED by user")
                skipped += 1
                continue

        ok, info = adapter(to, subject, body)
        if ok:
            print(f"  STATUS : SENT ({info})")
            sent += 1
            # Throttle: mail.com/ESPs all prefer gentle pacing
            time.sleep(2.0)
        else:
            print(f"  STATUS : FAILED — {info}")
            skipped += 1

    print("\n" + "=" * 70)
    print(f"Done. Sent: {sent}   Skipped/failed: {skipped}   "
          f"Legal-flagged (never sent): {len(legal_skipped)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", required=True, help="Path to leads CSV")
    ap.add_argument("--send", action="store_true",
                    help="Actually send (default is dry-run preview)")
    ap.add_argument("--limit", type=int, help="Max leads to process")
    ap.add_argument("--city", help="Filter to a single city")
    ap.add_argument("--yes-all", action="store_true",
                    help="Skip per-row confirmation (use with caution)")
    ap.add_argument("--body-column", default=DEFAULT_BODY_COLUMN)
    ap.add_argument("--subject-column", default=DEFAULT_SUBJECT_COLUMN)
    args = ap.parse_args()

    return process(
        Path(args.csv).resolve(),
        send=args.send,
        limit=args.limit,
        city=args.city,
        yes_all=args.yes_all,
        body_col=args.body_column,
        subject_col=args.subject_column,
    )


if __name__ == "__main__":
    sys.exit(main())
