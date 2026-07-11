"""Inbound webhooks for the AI Agency product line.

Every handler follows the same rule the rest of this codebase uses for
anything that touches Sheets/email/SMS: never write automatically. Each
handler normalizes the payload and drops a JSON artifact under output/ for
a human (or the agent, via connectors) to review and apply — the same
plan-then-apply pattern jetpakt_cli already uses for onboarding, sync, and
outreach. Nothing here calls Sheets, Outlook, Twilio, or Vapi to send
anything.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request

from billing.stripe_client import (
    WebhookVerificationError,
    customer_from_event,
    fetch_subscription,
    parse_webhook_event,
    subscription_from_event,
)
from jetpakt_cli.clients import build_onboarding_plan

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "output"
ONBOARDING_DIR = OUTPUT_DIR / "onboarding"
CALLS_DIR = OUTPUT_DIR / "calls"
SMS_DIR = OUTPUT_DIR / "sms"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(dir_path: Path, stem: str, data: dict) -> Path:
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / f"{stem}.json"
    path.write_text(json.dumps(data, indent=2))
    return path


# --- Stripe ------------------------------------------------------------------

SUBSCRIPTION_EVENTS = {"customer.subscription.created", "customer.subscription.updated"}


@router.post("/stripe")
async def stripe_webhook(request: Request, stripe_signature: str | None = Header(default=None)):
    payload = await request.body()
    try:
        event = parse_webhook_event(payload, stripe_signature)
    except WebhookVerificationError as exc:
        raise HTTPException(status_code=400, detail=f"invalid signature: {exc}") from exc

    event_type = event.get("type", "")

    if event_type in SUBSCRIPTION_EVENTS:
        subscription = subscription_from_event(event)
    elif event_type == "checkout.session.completed":
        obj = event.get("data", {}).get("object", {})
        subscription = fetch_subscription(obj.get("subscription"))
    else:
        return {"status": "ignored", "type": event_type}

    customer = customer_from_event(event)
    if customer is None or not customer.email:
        return {"status": "ignored", "type": event_type, "reason": "no customer email on event"}

    # No prospect match here — the agent applies this plan and reconciles
    # against the live Prospects tab, same as jetpakt onboard does offline.
    try:
        plan = build_onboarding_plan(customer, subscription, prospects=[])
    except ValueError as exc:
        # Product not yet in config.STRIPE_PRODUCT_TIER — a permanent config
        # gap, not a transient failure. Return 200 so Stripe doesn't retry;
        # the fix is a config change (or creating the product), not a resend.
        return {"status": "unconfigured", "type": event_type, "reason": str(exc)}

    out_path = _write_json(ONBOARDING_DIR, plan["summary"]["client_id"], plan)
    return {"status": "queued", "type": event_type, "onboarding_plan": str(out_path)}


# --- Vapi (AI phone agent) ----------------------------------------------------

@router.post("/vapi")
async def vapi_webhook(request: Request):
    body = await request.json()
    message = body.get("message", body)
    call = message.get("call", {}) if isinstance(message, dict) else {}
    call_id = call.get("id") or message.get("callId") or f"call_{_now_iso()}"

    record = {
        "received_at": _now_iso(),
        "call_id": call_id,
        "event_type": message.get("type") if isinstance(message, dict) else None,
        "phone_number": (call.get("customer") or {}).get("number") if isinstance(call, dict) else None,
        "duration_sec": message.get("durationSeconds") if isinstance(message, dict) else None,
        "ended_reason": message.get("endedReason") if isinstance(message, dict) else None,
        "transcript": message.get("transcript") if isinstance(message, dict) else None,
        "raw": body,
    }
    out_path = _write_json(CALLS_DIR, call_id.replace("/", "_"), record)
    return {"status": "queued", "call_id": call_id, "log": str(out_path)}


# --- Twilio (SMS status + inbound) --------------------------------------------

@router.post("/twilio")
async def twilio_webhook(request: Request):
    form = await request.form()
    data = dict(form)
    message_sid = data.get("MessageSid") or data.get("SmsSid") or f"sms_{_now_iso()}"

    record = {
        "received_at": _now_iso(),
        "message_sid": message_sid,
        "from": data.get("From"),
        "to": data.get("To"),
        "body": data.get("Body"),
        "status": data.get("MessageStatus") or data.get("SmsStatus"),
        "raw": data,
    }
    out_path = _write_json(SMS_DIR, message_sid, record)
    return {"status": "queued", "message_sid": message_sid, "log": str(out_path)}
