"""
JetPakt Stripe sync — read-side helper.

The MCP connector exposes read-only Stripe operations. This module:
  1. Fetches the JetPakt product catalog from Stripe and caches a small
     JSON lookup (price lookup_key → price_id, product_id, unit_amount).
  2. Checks whether a given Stripe customer has an active or trialing
     subscription for a given price lookup_key.

It never writes to Stripe. Catalog creation and customer/subscription
provisioning stay in the Stripe Dashboard, under Ryan's direct control
(that's the safer separation: billing writes require a human step, just
like email sends).

Usage:
    python stripe_sync.py --refresh          # pull catalog → data/stripe_catalog.json
    python stripe_sync.py --check <cust_id> <lookup_key>

The Pulse engine imports `billing_gate(account)` to decide whether a
cycle should run for an account with a billing config. Accounts with
no stripe_customer_id run unchanged (no gate) — this keeps the demo
roster working without any Stripe setup.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent
CATALOG_PATH = REPO / "data" / "stripe_catalog.json"
BILLING_LOG = REPO / "output" / "pulse" / "billing_gaps.jsonl"


# ---------- Canonical catalog (source of truth for lookup_keys) ----------

CANONICAL_PRODUCTS: list[dict[str, Any]] = [
    {
        "lookup_key": "jetpakt_scan_v1",
        "name": "JetPakt Scan",
        "unit_amount_usd": 49,
        "recurring": None,  # one-time
        "cadence_label": "one-time",
        "tier": 1,
        "vertical": "restaurant",
    },
    {
        "lookup_key": "jetpakt_pulse_essentials_v1",
        "name": "JetPakt Pulse Essentials",
        "unit_amount_usd": 149,
        "recurring": "month",
        "cadence_label": "monthly digest",
        "tier": 2,
        "vertical": "restaurant",
    },
    {
        "lookup_key": "jetpakt_pulse_pro_v1",
        "name": "JetPakt Pulse Pro",
        "unit_amount_usd": 399,
        "recurring": "month",
        "cadence_label": "weekly digest",
        "tier": 3,
        "vertical": "restaurant",
    },
    {
        "lookup_key": "jetpakt_pulse_alert_v1",
        "name": "JetPakt Pulse Alert",
        "unit_amount_usd": 899,
        "recurring": "month",
        "cadence_label": "weekly + on-alert",
        "tier": 4,
        "vertical": "restaurant",
    },
    {
        "lookup_key": "jetpakt_pulse_concierge_v1",
        "name": "JetPakt Pulse Concierge",
        "unit_amount_usd": 1499,
        "recurring": "month",
        "cadence_label": "weekly + alert + post-visit SMS",
        "tier": 5,
        "vertical": "restaurant",
    },
]

# AI Agency vertical (80134-area local service businesses: salons, dry
# cleaners, roofers, plumbers, trades). Each service is a setup/monthly pair
# except Review Autopilot (monthly add-on only). None of these lookup_keys
# exist in Stripe yet — same rule as the restaurant catalog: Ryan creates the
# matching products/prices by hand in the Dashboard (billing writes require a
# human step), then `--refresh` picks them up. See docs/AGENCY_CRM_SETUP.md.
AGENCY_PRODUCTS: list[dict[str, Any]] = [
    {
        "lookup_key": "jetpakt_agency_front_desk_setup_v1",
        "service_code": "front_desk", "kind": "setup",
        "name": "AI Front Desk — Setup",
        "unit_amount_usd": 997, "recurring": None, "vertical": "agency",
    },
    {
        "lookup_key": "jetpakt_agency_front_desk_monthly_v1",
        "service_code": "front_desk", "kind": "monthly",
        "name": "AI Front Desk — Monthly",
        "unit_amount_usd": 397, "recurring": "month", "vertical": "agency",
    },
    {
        "lookup_key": "jetpakt_agency_site_gbp_setup_v1",
        "service_code": "site_gbp", "kind": "setup",
        "name": "One-Page Site + GBP — Setup",
        "unit_amount_usd": 497, "recurring": None, "vertical": "agency",
    },
    {
        "lookup_key": "jetpakt_agency_site_gbp_monthly_v1",
        "service_code": "site_gbp", "kind": "monthly",
        "name": "One-Page Site + GBP — Monthly",
        "unit_amount_usd": 97, "recurring": "month", "vertical": "agency",
    },
    {
        "lookup_key": "jetpakt_agency_review_autopilot_monthly_v1",
        "service_code": "review_autopilot", "kind": "monthly",
        "name": "Review Autopilot — Monthly",
        "unit_amount_usd": 197, "recurring": "month", "vertical": "agency",
    },
    {
        "lookup_key": "jetpakt_agency_lead_intake_setup_v1",
        "service_code": "lead_intake", "kind": "setup",
        "name": "Lead Intake & Instant Quote — Setup",
        "unit_amount_usd": 297, "recurring": None, "vertical": "agency",
    },
    {
        "lookup_key": "jetpakt_agency_lead_intake_monthly_v1",
        "service_code": "lead_intake", "kind": "monthly",
        "name": "Lead Intake & Instant Quote — Monthly",
        "unit_amount_usd": 147, "recurring": "month", "vertical": "agency",
    },
    {
        "lookup_key": "jetpakt_agency_bundle_setup_v1",
        "service_code": "front_desk_complete", "kind": "setup",
        "name": "AI Front Desk Complete — Setup",
        "unit_amount_usd": 1997, "recurring": None, "vertical": "agency",
    },
    {
        "lookup_key": "jetpakt_agency_bundle_monthly_v1",
        "service_code": "front_desk_complete", "kind": "monthly",
        "name": "AI Front Desk Complete — Monthly",
        "unit_amount_usd": 497, "recurring": "month", "vertical": "agency",
    },
]


# ---------- Connector shim ----------

def _call(tool_name: str, args: dict) -> Any:
    """Call a Stripe MCP tool.

    This module is meant to be called from two contexts:
      1. The agent runtime, where `call_external_tool` is available.
      2. The CLI / cron, where it isn't. In that case we fall back to a
         pre-saved catalog and can't refresh.

    The shim avoids a hard import-time dependency on the agent runtime.
    """
    try:
        # Lazy import — only exists in the agent runtime
        from agent_runtime import call_external_tool  # type: ignore
    except Exception:
        raise RuntimeError(
            "Stripe MCP not available in this runtime — use the agent "
            "to refresh the catalog, or read the cached catalog instead."
        )
    return call_external_tool(
        tool_name=tool_name, source_id="stripe", arguments=args
    )


# ---------- Catalog fetch ----------

def fetch_prices_from_stripe() -> list[dict[str, Any]]:
    """Return all prices with lookup_keys matching the canonical set.

    Uses the list_prices + list_products tools (read-only).
    """
    want_keys = {p["lookup_key"] for p in CANONICAL_PRODUCTS + AGENCY_PRODUCTS}
    # list_prices has no lookup_key filter — we list all and filter client-side.
    # For a ~5-product shop this is trivially cheap.
    prices = _call("list_prices", {"limit": 100})
    matched: list[dict[str, Any]] = []
    for pr in prices or []:
        lk = pr.get("lookup_key")
        if lk in want_keys:
            matched.append(pr)
    return matched


def refresh_catalog() -> dict[str, Any]:
    """Pull Stripe catalog, build a lookup_key → metadata dict, save to disk."""
    prices = fetch_prices_from_stripe()
    by_key: dict[str, dict[str, Any]] = {}
    for pr in prices:
        lk = pr.get("lookup_key")
        if not lk:
            continue
        by_key[lk] = {
            "price_id": pr.get("id"),
            "product_id": pr.get("product"),
            "unit_amount": pr.get("unit_amount"),         # in cents
            "currency": pr.get("currency"),
            "recurring": (pr.get("recurring") or {}).get("interval"),
            "active": pr.get("active", True),
        }

    # Missing keys = products Ryan hasn't created in Dashboard yet.
    all_products = CANONICAL_PRODUCTS + AGENCY_PRODUCTS
    missing = [p["lookup_key"] for p in all_products
               if p["lookup_key"] not in by_key]

    out = {
        "refreshed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "by_lookup_key": by_key,
        "missing_lookup_keys": missing,
        "canonical": CANONICAL_PRODUCTS,
        "agency": AGENCY_PRODUCTS,
    }
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(out, indent=2))
    return out


def load_catalog() -> dict[str, Any] | None:
    if not CATALOG_PATH.exists():
        return None
    return json.loads(CATALOG_PATH.read_text())


# ---------- Subscription gate ----------

@dataclass
class BillingStatus:
    gate_applies: bool           # True if this account has a stripe config
    allowed: bool                # True if pulse cycle should run
    reason: str
    subscription_id: str | None = None
    subscription_status: str | None = None
    current_period_end: int | None = None


def check_subscription(customer_id: str | None,
                       price_lookup_key: str | None) -> BillingStatus:
    """Confirm a customer has an active/trialing subscription for the price.

    Returns a BillingStatus the caller can act on. When either arg is
    None, the gate doesn't apply (allowed=True).
    """
    if not customer_id or not price_lookup_key:
        return BillingStatus(
            gate_applies=False, allowed=True,
            reason="no billing config on account",
        )

    catalog = load_catalog()
    if not catalog:
        return BillingStatus(
            gate_applies=True, allowed=True,
            reason="catalog not yet synced — allowing run, log-only",
        )

    entry = catalog.get("by_lookup_key", {}).get(price_lookup_key)

    # Fallback: when lookup_keys aren't set in Stripe yet, the sync tool
    # maps product names back to canonical lookup_keys via name_to_lookup_key.
    # This keeps the gate functional during the setup window.
    if not entry:
        name_map = catalog.get("name_to_lookup_key", {})
        by_name = catalog.get("by_name", {})
        inverted = {v: k for k, v in name_map.items()}
        product_name = inverted.get(price_lookup_key)
        if product_name and product_name in by_name:
            entry = by_name[product_name]

    if not entry:
        return BillingStatus(
            gate_applies=True, allowed=True,
            reason=f"price {price_lookup_key!r} missing from catalog "
                   "— allowing run, log-only",
        )
    price_id = entry["price_id"]

    subs = _call("list_subscriptions", {
        "customer": customer_id,
        "price": price_id,
        "limit": 5,
    }) or []

    for s in subs:
        status = s.get("status")
        if status in ("active", "trialing"):
            return BillingStatus(
                gate_applies=True, allowed=True,
                reason=f"subscription {status}",
                subscription_id=s.get("id"),
                subscription_status=status,
                current_period_end=s.get("current_period_end"),
            )

    # Found no active sub — pull the most-recent one (if any) for context.
    latest = subs[0] if subs else None
    return BillingStatus(
        gate_applies=True, allowed=False,
        reason="no active/trialing subscription for this price",
        subscription_id=(latest or {}).get("id"),
        subscription_status=(latest or {}).get("status"),
    )


def log_billing_gap(account_id: str, status: BillingStatus) -> None:
    BILLING_LOG.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "account_id": account_id,
        "allowed": status.allowed,
        "reason": status.reason,
        "subscription_id": status.subscription_id,
        "subscription_status": status.subscription_status,
    }
    with BILLING_LOG.open("a") as f:
        f.write(json.dumps(rec) + "\n")


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="JetPakt Stripe catalog sync.")
    ap.add_argument("--refresh", action="store_true",
                    help="Pull catalog from Stripe and save to disk.")
    ap.add_argument("--show", action="store_true",
                    help="Print the cached catalog.")
    ap.add_argument("--check", nargs=2, metavar=("CUSTOMER_ID", "LOOKUP_KEY"),
                    help="Check a customer's subscription status.")
    args = ap.parse_args(argv)

    if args.refresh:
        try:
            out = refresh_catalog()
        except RuntimeError as e:
            print(f"Cannot refresh from CLI: {e}")
            return 2
        print(f"Catalog refreshed → {CATALOG_PATH}")
        print(f"  present keys:  {list(out['by_lookup_key'].keys())}")
        print(f"  missing keys:  {out['missing_lookup_keys']}")
        return 0

    if args.show:
        cat = load_catalog()
        if not cat:
            print("No catalog on disk. Run --refresh first.")
            return 1
        print(json.dumps(cat, indent=2))
        return 0

    if args.check:
        cust, lk = args.check
        try:
            st = check_subscription(cust, lk)
        except RuntimeError as e:
            print(f"Cannot check from CLI: {e}")
            return 2
        print(f"  gate_applies:        {st.gate_applies}")
        print(f"  allowed:             {st.allowed}")
        print(f"  reason:              {st.reason}")
        print(f"  subscription_id:     {st.subscription_id}")
        print(f"  subscription_status: {st.subscription_status}")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
