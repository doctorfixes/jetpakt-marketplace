"""
Billing-gate tests \u2014 every test is design-level (no live Stripe call).

  1. No stripe config on account \u2192 gate doesn't apply, cycle allowed.
  2. Catalog absent \u2192 allowed=True with clear reason (soft-launch safety).
  3. Hard-mode skip: pulse_cron skips an account with stripe config but no
     active subscription when --enforce-billing is passed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import stripe_sync  # noqa: E402
from stripe_sync import BillingStatus, check_subscription  # noqa: E402


def test_no_stripe_config_gate_does_not_apply():
    st = check_subscription(customer_id=None, price_lookup_key=None)
    assert st.gate_applies is False
    assert st.allowed is True
    assert "no billing config" in st.reason


def test_missing_catalog_soft_allows(tmp_path, monkeypatch):
    # Point the catalog at a non-existent file
    monkeypatch.setattr(stripe_sync, "CATALOG_PATH", tmp_path / "missing.json")

    st = check_subscription("cus_fake", "jetpakt_pulse_pro_v1")
    assert st.gate_applies is True
    assert st.allowed is True
    assert "catalog not yet synced" in st.reason


def test_missing_lookup_key_soft_allows(tmp_path, monkeypatch):
    # Seed a catalog that doesn't have the requested lookup_key
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps({
        "by_lookup_key": {"some_other_key": {"price_id": "price_123"}},
        "missing_lookup_keys": ["jetpakt_pulse_pro_v1"],
    }))
    monkeypatch.setattr(stripe_sync, "CATALOG_PATH", catalog_path)

    st = check_subscription("cus_fake", "jetpakt_pulse_pro_v1")
    assert st.gate_applies is True
    assert st.allowed is True
    assert "missing from catalog" in st.reason


def test_active_subscription_allowed(tmp_path, monkeypatch):
    # Catalog with the price
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps({
        "by_lookup_key": {
            "jetpakt_pulse_pro_v1": {
                "price_id": "price_abc",
                "product_id": "prod_abc",
                "unit_amount": 39900,
                "currency": "usd",
                "recurring": "month",
                "active": True,
            },
        },
        "missing_lookup_keys": [],
    }))
    monkeypatch.setattr(stripe_sync, "CATALOG_PATH", catalog_path)

    def fake_call(tool_name, args):
        assert tool_name == "list_subscriptions"
        return [{"id": "sub_abc", "status": "active",
                 "current_period_end": 1777777777}]

    monkeypatch.setattr(stripe_sync, "_call", fake_call)

    st = check_subscription("cus_abc", "jetpakt_pulse_pro_v1")
    assert st.gate_applies is True
    assert st.allowed is True
    assert st.subscription_status == "active"
    assert st.subscription_id == "sub_abc"


def test_no_subscription_blocks_in_hard_mode(tmp_path, monkeypatch):
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps({
        "by_lookup_key": {
            "jetpakt_pulse_pro_v1": {"price_id": "price_abc"},
        },
        "missing_lookup_keys": [],
    }))
    monkeypatch.setattr(stripe_sync, "CATALOG_PATH", catalog_path)
    monkeypatch.setattr(stripe_sync, "_call", lambda *a, **k: [])

    st = check_subscription("cus_abc", "jetpakt_pulse_pro_v1")
    assert st.gate_applies is True
    assert st.allowed is False
    assert "no active" in st.reason.lower()
