"""
JetPakt Pulse — CLI entry point.

Runs the Pulse pipeline for all accounts matching a cadence, renders a
PDF per account, composes an Outlook draft payload per account, and
writes a human-reviewable .md preview to output/pulse/drafts/.

Use:
    python pulse_cron.py --cadence weekly
    python pulse_cron.py --cadence monthly
    python pulse_cron.py --account big_daddys_colfax     # one-off
    python pulse_cron.py --cadence weekly --dry-run       # skip PDF & drafts

This is the entry point the scheduler (schedule_cron) can call. By
design it never auto-sends emails; drafts are staged to disk and
surfaced for Ryan's approval in a separate human step.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pulse_engine import (
    Account, PulseInsight, filter_accounts_for_cadence, load_accounts,
    run_for_account,
)
from pulse_report import render_pulse_pdf
from pulse_deliver import build_draft, write_draft_to_disk

try:
    from stripe_sync import check_subscription, log_billing_gap
    _STRIPE_AVAILABLE = True
except Exception:
    _STRIPE_AVAILABLE = False


REPO = Path(__file__).resolve().parent
OUTPUT_DIR = REPO / "output" / "pulse"
DRAFTS_DIR = OUTPUT_DIR / "drafts"
RUN_LOG = OUTPUT_DIR / "pulse_runs.jsonl"


def _pdf_path(account_id: str, snapshot_date: str) -> str:
    return str(OUTPUT_DIR / f"{account_id}_{snapshot_date}.pdf")


def _run_one(account: Account, dry_run: bool,
             enforce_billing: bool = False) -> dict[str, Any]:
    # --- Optional Stripe billing gate -------------------------------------
    # Only applies when the account has both stripe_customer_id and a
    # price lookup_key set. Accounts without them run unchanged.
    # enforce_billing=False means we log the gap but still run the cycle
    # (demo / soft-launch mode). enforce_billing=True skips the cycle.
    if _STRIPE_AVAILABLE and account.stripe_customer_id and account.stripe_price_lookup_key:
        try:
            status = check_subscription(
                account.stripe_customer_id, account.stripe_price_lookup_key)
            log_billing_gap(account.account_id, status)
            if status.gate_applies and not status.allowed and enforce_billing:
                return {
                    "account_id": account.account_id,
                    "skipped": True,
                    "reason": f"billing gate: {status.reason}",
                }
        except Exception as e:  # noqa: BLE001 — billing check should never block a run
            print(f"    (billing check failed: {e!r} — continuing)")

    insight = run_for_account(account)
    record: dict[str, Any] = {
        "account_id": account.account_id,
        "cadence": account.cadence,
        "tier": account.tier,
        "snapshot_date": insight.snapshot_date,
        "is_first_run": insight.is_first_run,
        "overall_severity": insight.overall_severity,
        "requires_same_day_alert": insight.requires_same_day_alert,
        "n_changes": len(insight.changes),
        "has_legal_high": any(
            f.get("flag") == "LEGAL-HIGH" for f in insight.legal_flags
        ),
    }

    if dry_run:
        record["dry_run"] = True
        return record

    pdf = _pdf_path(account.account_id, insight.snapshot_date)
    render_pulse_pdf(insight, pdf)
    record["pdf"] = pdf

    payload = build_draft(insight, pdf)
    md = write_draft_to_disk(payload, DRAFTS_DIR)
    record["draft_md"] = md
    record["draft_to"] = payload.to
    record["draft_cc"] = payload.cc
    record["draft_subject"] = payload.subject
    record["draft_requires_human_review"] = payload.requires_human_review
    record["draft_routing_reason"] = payload.routing_reason
    return record


def _log_run(records: list[dict[str, Any]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    with RUN_LOG.open("a") as f:
        for r in records:
            f.write(json.dumps({"ts": ts, **r}) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run JetPakt Pulse cycle.")
    ap.add_argument("--cadence", choices=["weekly", "monthly"],
                    help="Run all accounts on this cadence.")
    ap.add_argument("--account", help="Run one specific account_id (overrides --cadence).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Skip PDF render and draft write; just diff.")
    ap.add_argument("--enforce-billing", action="store_true",
                    help="Skip accounts with no active Stripe subscription "
                         "(default: log the gap but still run).")
    args = ap.parse_args(argv)

    accounts = load_accounts()
    if args.account:
        targets = [a for a in accounts if a.account_id == args.account]
        if not targets:
            print(f"ERROR: no account with id {args.account!r}. "
                  f"Available: {[a.account_id for a in accounts]}")
            return 2
    elif args.cadence:
        targets = filter_accounts_for_cadence(accounts, args.cadence)
    else:
        ap.error("must pass --cadence or --account")
        return 2

    if not targets:
        print("No accounts matched. Nothing to do.")
        return 0

    print(f"Pulse run · {len(targets)} account(s) · dry_run={args.dry_run}")
    records: list[dict[str, Any]] = []
    for acct in targets:
        print(f"  → {acct.account_id} (tier {acct.tier}, {acct.cadence})")
        try:
            rec = _run_one(acct, dry_run=args.dry_run,
                           enforce_billing=args.enforce_billing)
            records.append(rec)
            if rec.get("skipped"):
                print(f"    skipped: {rec['reason']}")
                continue
            tag = ""
            if rec.get("draft_requires_human_review"):
                tag = " · REVIEW"
            if rec["overall_severity"] == "HIGH":
                tag += " · HIGH"
            print(f"    severity={rec['overall_severity']} "
                  f"changes={rec['n_changes']}{tag}")
        except Exception as e:  # noqa: BLE001 — isolate per-account failures
            print(f"    FAILED: {e!r}")
            records.append({
                "account_id": acct.account_id,
                "error": repr(e),
            })

    _log_run(records)
    print(f"Done. Draft previews in: {DRAFTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
