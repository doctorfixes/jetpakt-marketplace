"""AI Agency service catalog endpoint.

Groups stripe_sync.AGENCY_PRODUCTS (setup + monthly price pairs) into the
service cards the marketing site renders. Prices here are the *canonical*
list price — the source of truth for what to charge — independent of
whether the matching Stripe products exist yet.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

import stripe_sync

router = APIRouter(prefix="/api/services", tags=["services"])


def _grouped_catalog() -> list[dict]:
    by_code: dict[str, dict] = {}
    for p in stripe_sync.AGENCY_PRODUCTS:
        code = p["service_code"]
        row = by_code.setdefault(code, {
            "code": code,
            "name": p["name"].split(" — ")[0],
            "setup_usd": 0,
            "monthly_usd": 0,
        })
        if p["kind"] == "setup":
            row["setup_usd"] = p["unit_amount_usd"]
        elif p["kind"] == "monthly":
            row["monthly_usd"] = p["unit_amount_usd"]
    # Stable order: individual services first, bundle last.
    order = ["front_desk", "site_gbp", "review_autopilot", "lead_intake", "front_desk_complete"]
    return [by_code[c] for c in order if c in by_code]


@router.get("")
async def list_services():
    return {"services": _grouped_catalog()}


@router.get("/{code}")
async def get_service(code: str):
    for svc in _grouped_catalog():
        if svc["code"] == code:
            return svc
    raise HTTPException(status_code=404, detail=f"Unknown service code: {code}")
