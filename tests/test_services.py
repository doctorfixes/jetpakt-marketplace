"""Tests for the AI Agency service catalog endpoint."""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_list_services_returns_all_five():
    r = client.get("/api/services")
    assert r.status_code == 200
    codes = [s["code"] for s in r.json()["services"]]
    assert codes == ["front_desk", "site_gbp", "review_autopilot", "lead_intake", "front_desk_complete"]


def test_bundle_pricing_matches_plan():
    r = client.get("/api/services/front_desk_complete")
    assert r.status_code == 200
    body = r.json()
    assert body["setup_usd"] == 1997
    assert body["monthly_usd"] == 497


def test_review_autopilot_has_no_setup_fee():
    r = client.get("/api/services/review_autopilot")
    assert r.json()["setup_usd"] == 0


def test_unknown_service_code_404s():
    r = client.get("/api/services/does_not_exist")
    assert r.status_code == 404
