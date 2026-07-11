"""Tests for the AI Agency inbound webhooks.

Every handler writes a plan/log JSON artifact instead of calling out to
Sheets/Outlook/Twilio/Vapi directly (see api/routes/webhooks.py docstring),
so these tests redirect the output directories into a tmp_path and assert
on what got written.
"""
import json

import pytest
from fastapi.testclient import TestClient

import api.routes.webhooks as webhooks
import jetpakt_cli.config as cfg
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _redirect_output_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(webhooks, "ONBOARDING_DIR", tmp_path / "onboarding")
    monkeypatch.setattr(webhooks, "CALLS_DIR", tmp_path / "calls")
    monkeypatch.setattr(webhooks, "SMS_DIR", tmp_path / "sms")
    yield tmp_path


def _subscription_event(product_id: str, sub_id: str = "sub_test_1") -> dict:
    return {
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": sub_id,
                "customer": "cus_test_1",
                "customer_details": {"email": "owner@parkerplumbingco.com", "name": "Parker Plumbing Co"},
                "status": "active",
                "items": {"data": [{"price": {"id": "price_test", "product": product_id}}]},
            }
        },
    }


def test_stripe_webhook_known_product_writes_onboarding_plan(tmp_path, monkeypatch):
    monkeypatch.setitem(cfg.STRIPE_PRODUCT_TIER, "prod_test_known", ("AI Front Desk Complete", 30, 497))
    r = client.post("/api/webhooks/stripe", content=json.dumps(_subscription_event("prod_test_known")))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "queued"
    written = json.loads((tmp_path / "onboarding").glob("*.json").__next__().read_text())
    assert written["summary"]["tier"] == "AI Front Desk Complete"
    assert written["summary"]["mrr_usd"] == 497


def test_stripe_webhook_unknown_product_does_not_crash():
    r = client.post("/api/webhooks/stripe", content=json.dumps(_subscription_event("prod_never_seen")))
    assert r.status_code == 200
    assert r.json()["status"] == "unconfigured"


def test_stripe_webhook_ignores_unrelated_event_types():
    event = {"type": "invoice.paid", "data": {"object": {}}}
    r = client.post("/api/webhooks/stripe", content=json.dumps(event))
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


def test_vapi_webhook_writes_call_log(tmp_path):
    body = {
        "message": {
            "type": "end-of-call-report",
            "call": {"id": "call_xyz", "customer": {"number": "+17205551234"}},
            "durationSeconds": 42,
            "endedReason": "customer-ended-call",
        }
    }
    r = client.post("/api/webhooks/vapi", json=body)
    assert r.status_code == 200
    assert r.json()["call_id"] == "call_xyz"
    written = json.loads((tmp_path / "calls" / "call_xyz.json").read_text())
    assert written["duration_sec"] == 42
    assert written["phone_number"] == "+17205551234"


def test_twilio_webhook_writes_sms_log(tmp_path):
    r = client.post(
        "/api/webhooks/twilio",
        data={"MessageSid": "SM999", "From": "+17205551234", "To": "+17205559999",
              "Body": "YES", "MessageStatus": "delivered"},
    )
    assert r.status_code == 200
    assert r.json()["message_sid"] == "SM999"
    written = json.loads((tmp_path / "sms" / "SM999.json").read_text())
    assert written["body"] == "YES"
    assert written["status"] == "delivered"
