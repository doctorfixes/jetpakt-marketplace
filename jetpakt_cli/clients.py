"""Client lifecycle module.

Turns a Stripe customer+subscription into a Clients row + a scheduled first
deliverable + a welcome-email draft. Follows the same offline plan/apply
pattern as inbox.py: the agent runs Stripe + Sheets + Outlook connector calls,
this module does all the deterministic logic.

Inputs (passed as JSON files):
  - stripe_customer.json: single object with Stripe customer fields
  - stripe_subscription.json: single object with Stripe subscription fields
    (or null for one-time Scan purchases)
  - prospects.json: list of prospects (reuse inbox.py schema) so we can
    match by contact_email -> prospect_id

Outputs:
  - onboarding_plan.json: {clients_append, prospect_updates, outlook_drafts,
    summary}

Stage transitions: Drafted|Sent|Replied -> Client (never overrides
Disqualified).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config as cfg


# --- Dataclasses -----------------------------------------------------------

@dataclass(frozen=True)
class StripeCustomer:
    id: str
    email: str
    name: str = ""
    phone: str = ""


@dataclass(frozen=True)
class StripeSubscription:
    id: str
    customer_id: str
    product_id: str
    price_id: str
    status: str
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None


@dataclass(frozen=True)
class ProspectLite:
    prospect_id: str
    business_name: str
    owner_email: str
    stage: str


@dataclass(frozen=True)
class OnboardingRow:
    client_id: str
    prospect_id: str
    business_name: str
    contact_email: str
    stripe_customer_id: str
    stripe_subscription_id: str
    tier: str
    cadence: str           # "one_time" | "weekly" | "monthly"
    mrr_usd: int
    status: str            # "Active" | "Trialing" | "Scan"
    onboarded_at: str
    next_deliverable_due: str
    notes: str

    def as_row(self, now_iso: str) -> List[str]:
        """Emit positional 18-cell row matching cfg.CLIENTS_COLUMNS."""
        return [
            self.client_id, self.prospect_id, self.business_name,
            self.contact_email, self.stripe_customer_id,
            self.stripe_subscription_id, self.tier, self.cadence,
            str(self.mrr_usd), self.status, self.onboarded_at,
            self.next_deliverable_due, "", "", "", self.notes,
            now_iso, now_iso,
        ]


# --- Helpers ---------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:40]


def _client_id(stripe_customer_id: str, product_id: str) -> str:
    # Deterministic so re-running onboarding is idempotent.
    h = hashlib.sha1(f"{stripe_customer_id}::{product_id}".encode()).hexdigest()[:8]
    return f"client_{h}"


def _cadence_label(cadence_days: Optional[int]) -> str:
    return (
        "one_time" if cadence_days is None
        else "weekly" if cadence_days == 7
        else "monthly"
    )


def _tier_from_subscription(sub: Optional[StripeSubscription]) -> tuple:
    """Return (tier_label, cadence_days, mrr_usd, cadence_label, status)."""
    if sub is None:
        label, cadence_days, mrr = cfg.NO_SUBSCRIPTION_TIER
        return (label, cadence_days, mrr, _cadence_label(cadence_days), label)
    product_id = sub.product_id
    if product_id not in cfg.STRIPE_PRODUCT_TIER:
        raise ValueError(
            f"Unknown Stripe product_id {product_id!r}. Add to "
            f"config.STRIPE_PRODUCT_TIER before onboarding."
        )
    label, cadence_days, mrr = cfg.STRIPE_PRODUCT_TIER[product_id]
    status_label = "Trialing" if sub.status == "trialing" else "Active"
    return (label, cadence_days, mrr, _cadence_label(cadence_days), status_label)


def _first_due_iso(cadence_days: Optional[int], now: datetime) -> str:
    # First memo due 2 business days from onboarding for Scan; otherwise
    # cadence_days from now. Rounded to 09:00 UTC for easy cron scheduling.
    if cadence_days is None:
        target = now + timedelta(days=2)
    else:
        target = now + timedelta(days=cadence_days)
    target = target.replace(hour=9, minute=0, second=0, microsecond=0)
    return target.isoformat(timespec="seconds")


# --- Loaders ---------------------------------------------------------------

def load_stripe_customer(path: Path) -> StripeCustomer:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return StripeCustomer(
        id=raw["id"],
        email=raw.get("email", "") or "",
        name=raw.get("name", "") or "",
        phone=raw.get("phone", "") or "",
    )


def load_stripe_subscription(path: Optional[Path]) -> Optional[StripeSubscription]:
    if path is None or not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw is None:
        return None
    # Stripe subscriptions have items.data[].price.product; callers should
    # normalize to the simple schema below before passing in.
    return StripeSubscription(
        id=raw["id"],
        customer_id=raw["customer_id"],
        product_id=raw["product_id"],
        price_id=raw["price_id"],
        status=raw.get("status", "active"),
        current_period_start=raw.get("current_period_start"),
        current_period_end=raw.get("current_period_end"),
    )


def load_prospects(path: Path) -> List[ProspectLite]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for p in raw:
        out.append(ProspectLite(
            prospect_id=p["prospect_id"],
            business_name=p.get("business_name", ""),
            owner_email=(p.get("owner_email", "") or "").strip().lower(),
            stage=p.get("stage", ""),
        ))
    return out


def match_prospect(customer_email: str,
                   prospects: List[ProspectLite]) -> Optional[ProspectLite]:
    """Match a Stripe customer to a Prospects row by email.

    Stripe emails are user-supplied so we compare case-insensitively.
    Returns None if no match (signup from a net-new visitor who never got
    cold outreach).
    """
    needle = (customer_email or "").strip().lower()
    if not needle:
        return None
    for p in prospects:
        if p.owner_email and p.owner_email == needle:
            return p
    return None


# --- Welcome email draft ---------------------------------------------------
# Template text lives in config.py — it's profile-specific (restaurant vs.
# agency copy) while this formatting logic stays shared.


def build_welcome_draft(row: OnboardingRow, sub_opt: Optional[StripeSubscription]) -> Dict[str, Any]:
    cadence_human = {
        "one_time": "one-time",
        "weekly": "weekly",
        "monthly": "monthly",
    }[row.cadence]
    due_human = row.next_deliverable_due.split("T")[0]
    body = cfg.WELCOME_BODY_TEMPLATE.format(
        tier_name=row.tier,
        first_due_human=due_human,
        cadence_human=cadence_human,
        client_id=row.client_id,
    )
    # No em/en-dashes per outreach policy; keep under 45 chars.
    subject = cfg.WELCOME_SUBJECT_TEMPLATE.format(tier_name=row.tier, first_due_human=due_human)
    if len(subject) > 45:
        subject = f"{row.tier} is active"
    # Guard against any stray em/en dashes in future template tweaks.
    assert "—" not in subject and "–" not in subject, subject
    sub_hash = hashlib.sha1(subject.encode()).hexdigest()[:8]
    return {
        "action": "draft_email",
        "to": [row.contact_email],
        "cc": [],
        "bcc": [],
        "subject": subject,
        "body": body,
        "idempotency_key": f"welcome::{row.client_id}::{sub_hash}",
        "client_id": row.client_id,
    }


# --- Plan builder ----------------------------------------------------------

def build_onboarding_plan(customer: StripeCustomer,
                          subscription: Optional[StripeSubscription],
                          prospects: List[ProspectLite],
                          now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    now_iso = now.isoformat(timespec="seconds")

    tier_label, cadence_days, mrr_usd, cadence_label, status_label = _tier_from_subscription(subscription)

    matched = match_prospect(customer.email, prospects)
    if matched:
        prospect_id = matched.prospect_id
        business_name = matched.business_name
        prospect_current_stage = matched.stage
    else:
        # Net-new buyer: synthesize a prospect_id from the email domain + name.
        domain_slug = _slugify((customer.email or "unknown").split("@")[-1])
        name_slug = _slugify(customer.name) or "new_client"
        prospect_id = f"direct_{domain_slug}_{name_slug}"[:60]
        business_name = customer.name or customer.email or prospect_id
        prospect_current_stage = ""

    product_id = subscription.product_id if subscription else cfg.DEFAULT_ONE_TIME_PRODUCT_ID
    client_id = _client_id(customer.id, product_id)

    row = OnboardingRow(
        client_id=client_id,
        prospect_id=prospect_id,
        business_name=business_name,
        contact_email=customer.email,
        stripe_customer_id=customer.id,
        stripe_subscription_id=subscription.id if subscription else "",
        tier=tier_label,
        cadence=cadence_label,
        mrr_usd=mrr_usd,
        status=status_label,
        onboarded_at=now_iso,
        next_deliverable_due=_first_due_iso(cadence_days, now),
        notes=f"Onboarded {now_iso}. Product={product_id}.",
    )

    # Prospect update: flip to Client unless currently Disqualified or no match.
    prospect_updates = []
    if matched and prospect_current_stage.lower() != "disqualified":
        prospect_updates.append({
            "find": {"column": "A", "value": matched.prospect_id},
            "set": {
                "stage": "Client",
                "stage_entered_at": now_iso,
                "notes_append": f"Converted to Client {now_iso} "
                                f"({tier_label} {cadence_label} ${mrr_usd}/mo)",
                "updated_at": now_iso,
            },
        })

    welcome = build_welcome_draft(row, subscription)

    return {
        "generated_at": now_iso,
        "clients_append": [{
            "row_object": {k: v for k, v in zip(cfg.CLIENTS_COLUMNS, row.as_row(now_iso))},
            "positional_row": row.as_row(now_iso),
        }],
        "prospect_updates": prospect_updates,
        "outlook_drafts": [welcome],
        "summary": {
            "client_id": client_id,
            "prospect_id": prospect_id,
            "tier": tier_label,
            "cadence": cadence_label,
            "mrr_usd": mrr_usd,
            "matched_prospect": matched is not None,
            "next_deliverable_due": row.next_deliverable_due,
        },
    }
