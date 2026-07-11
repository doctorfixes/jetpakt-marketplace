"""Stripe webhook client for the AI Agency product line.

Normalizes raw Stripe webhook payloads into the StripeCustomer /
StripeSubscription shapes jetpakt_cli.clients.build_onboarding_plan expects,
so a webhook hit is a straight line: verify -> normalize -> onboarding plan.

Products/prices are created by hand in the Stripe Dashboard, same rule
stripe_sync.py documents for the restaurant business: billing writes require
a human step. This module only ever reads.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import stripe

from jetpakt_cli.clients import StripeCustomer, StripeSubscription

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# DEV_MODE skips signature verification and live API calls so the webhook
# route is exercisable with `stripe trigger` / hand-built JSON before real
# keys exist. Never true once STRIPE_WEBHOOK_SECRET is configured.
DEV_MODE = not bool(STRIPE_WEBHOOK_SECRET)

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class WebhookVerificationError(Exception):
    """Raised when a webhook payload's signature can't be verified."""


def parse_webhook_event(payload: bytes, sig_header: Optional[str]) -> dict[str, Any]:
    """Verify and parse a raw Stripe webhook request body into an event dict."""
    if DEV_MODE:
        return json.loads(payload)
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise WebhookVerificationError(str(exc)) from exc
    return event


def customer_from_event(event: dict[str, Any]) -> Optional[StripeCustomer]:
    """Extract a StripeCustomer from a checkout.session.* or customer.* event."""
    obj = event.get("data", {}).get("object", {})
    customer_id = obj.get("customer") or (obj.get("object") == "customer" and obj.get("id"))
    if not customer_id:
        return None
    details = obj.get("customer_details") or {}
    return StripeCustomer(
        id=customer_id,
        email=(details.get("email") or obj.get("customer_email") or obj.get("email") or "") or "",
        name=details.get("name") or obj.get("name") or "",
        phone=details.get("phone") or obj.get("phone") or "",
    )


def _normalize_subscription(sub: dict[str, Any]) -> Optional[StripeSubscription]:
    items = (sub.get("items") or {}).get("data") or []
    if not items:
        return None
    price = items[0].get("price") or {}
    product = price.get("product")
    # Product can arrive as an id string or an expanded object.
    product_id = product.get("id") if isinstance(product, dict) else product
    return StripeSubscription(
        id=sub.get("id", ""),
        customer_id=sub.get("customer", ""),
        product_id=product_id or "",
        price_id=price.get("id", ""),
        status=sub.get("status", "active"),
        current_period_start=str(sub.get("current_period_start") or "") or None,
        current_period_end=str(sub.get("current_period_end") or "") or None,
    )


def subscription_from_event(event: dict[str, Any]) -> Optional[StripeSubscription]:
    """Extract a StripeSubscription straight from a customer.subscription.* event.

    Prefer this over checkout.session.completed: checkout sessions only carry
    a subscription id, not its line items, so a tier can't be resolved from
    one without an extra API call (see fetch_subscription below).
    """
    if not event.get("type", "").startswith("customer.subscription."):
        return None
    return _normalize_subscription(event.get("data", {}).get("object", {}))


def fetch_subscription(subscription_id: str) -> Optional[StripeSubscription]:
    """Fetch and normalize a subscription by id via the live Stripe API.

    Used when all a handler has is a checkout.session.completed event's
    bare `subscription` id. Returns None in DEV_MODE (no live API calls).
    """
    if DEV_MODE or not STRIPE_SECRET_KEY or not subscription_id:
        return None
    sub = stripe.Subscription.retrieve(subscription_id, expand=["items.data.price"])
    return _normalize_subscription(sub)
