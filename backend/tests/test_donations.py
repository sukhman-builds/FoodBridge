import threading
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import create_app


def post_donation(client, payload):
    return client.post("/donations", json=payload)


# ---------------------------------------------------------------- health
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------- create
def test_create_donation_returns_201_and_stored_fields(client, make_payload):
    r = post_donation(client, make_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["status"] == "available"
    assert body["food_name"] == "Vegetable biryani"
    assert body["servings"] == 40
    assert body["location"] == "12 Example Street, Sample Town"
    assert body["pickup_deadline"].startswith("2030-01-01T14:00:00")
    assert body["claimed_by"] is None


def test_create_does_not_leak_donor_contact(client, make_payload):
    body = post_donation(client, make_payload()).json()
    assert "donor_contact" not in body
    assert "donor@example.com" not in client.get("/donations").text
    assert "donor@example.com" not in client.get(f"/donations/{body['id']}").text


def test_create_trims_whitespace(client, make_payload):
    body = post_donation(client, make_payload(food_name="  Soup  ")).json()
    assert body["food_name"] == "Soup"


def test_create_accepts_phone_contact(client, make_payload):
    assert post_donation(client, make_payload(donor_contact="+91 98765 43210")).status_code == 201


def test_category_is_optional(client, make_payload):
    payload = make_payload()
    del payload["category"]
    r = post_donation(client, payload)
    assert r.status_code == 201
    assert r.json()["category"] is None


# ------------------------------------------------------------ validation
@pytest.mark.parametrize(
    "field", ["food_name", "description", "servings", "location",
              "pickup_deadline", "donor_name", "donor_contact"],
)
def test_missing_required_field_is_422(client, make_payload, field):
    payload = make_payload()
    del payload[field]
    assert post_donation(client, payload).status_code == 422


@pytest.mark.parametrize(
    "overrides",
    [
        {"servings": 0},
        {"servings": -5},
        {"servings": "ten"},
        {"servings": "10"},       # strings are not silently coerced
        {"servings": 2.5},
        {"servings": 1_000_000},
        {"food_name": ""},
        {"food_name": "   "},
        {"food_name": "x" * 121},
        {"description": ""},
        {"description": "x" * 501},
        {"location": "  "},
        {"donor_name": ""},
        {"donor_contact": "hello"},
        {"donor_contact": "12345"},
        {"pickup_deadline": "not-a-date"},
        {"unexpected_field": "nope"},
    ],
)
def test_invalid_values_rejected_and_nothing_stored(client, make_payload, overrides):
    r = post_donation(client, make_payload(**overrides))
    assert r.status_code == 422
    assert client.get("/donations").json() == []


def test_past_deadline_rejected(client, make_payload, fake_clock):
    past = (fake_clock.now - timedelta(minutes=1)).isoformat()
    r = post_donation(client, make_payload(pickup_deadline=past))
    assert r.status_code == 422
    assert "future" in r.text


def test_deadline_without_timezone_rejected(client, make_payload):
    r = post_donation(client, make_payload(pickup_deadline="2030-01-01T18:00:00"))
    assert r.status_code == 422
    assert "timezone" in r.text


def test_deadline_more_than_7_days_ahead_rejected(client, make_payload, fake_clock):
    far = (fake_clock.now + timedelta(days=8)).isoformat()
    assert post_donation(client, make_payload(pickup_deadline=far)).status_code == 422


def test_malformed_json_is_422(client):
    r = client.post("/donations", content="{bad", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


# ------------------------------------------------------------------ list
def test_list_empty(client):
    r = client.get("/donations")
    assert r.status_code == 200
    assert r.json() == []


def test_list_newest_first(client, make_payload):
    post_donation(client, make_payload(food_name="First"))
    post_donation(client, make_payload(food_name="Second"))
    names = [d["food_name"] for d in client.get("/donations").json()]
    assert names == ["Second", "First"]


def test_list_status_filter(client, make_payload):
    post_donation(client, make_payload(food_name="A"))
    post_donation(client, make_payload(food_name="B"))
    client.post("/donations/1/claim", json={"claimed_by": "Test NGO"})

    available = client.get("/donations", params={"status": "available"}).json()
    claimed = client.get("/donations", params={"status": "claimed"}).json()
    assert [d["food_name"] for d in available] == ["B"]
    assert [d["food_name"] for d in claimed] == ["A"]


def test_list_invalid_status_is_422(client):
    assert client.get("/donations", params={"status": "bogus"}).status_code == 422


def test_list_pagination(client, make_payload):
    for i in range(5):
        post_donation(client, make_payload(food_name=f"Item {i}"))
    page = client.get("/donations", params={"limit": 2, "offset": 2}).json()
    assert [d["food_name"] for d in page] == ["Item 2", "Item 1"]
    assert client.get("/donations", params={"limit": 0}).status_code == 422
    assert client.get("/donations", params={"limit": 101}).status_code == 422


# ----------------------------------------------------------------- get
def test_get_donation(client, make_payload):
    created = post_donation(client, make_payload()).json()
    r = client.get(f"/donations/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created


def test_get_missing_is_404(client):
    r = client.get("/donations/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Donation not found"


@pytest.mark.parametrize("bad_id", ["abc", "0", "-1", "99999999999999999999999"])
def test_get_invalid_id_is_422_not_500(client, bad_id):
    assert client.get(f"/donations/{bad_id}").status_code == 422


# --------------------------------------------------------------- claim
def test_claim_success(client, make_payload):
    donation_id = post_donation(client, make_payload()).json()["id"]
    r = client.post(f"/donations/{donation_id}/claim", json={"claimed_by": "  Test NGO "})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "claimed"
    assert body["claimed_by"] == "Test NGO"
    assert body["claimed_at"] is not None
    # Pickup contact is revealed only to the claimer
    assert body["donor_contact"] == "donor@example.com"
    # and the change is persisted
    assert client.get(f"/donations/{donation_id}").json()["status"] == "claimed"


def test_claim_twice_returns_409_and_keeps_first_claimer(client, make_payload):
    donation_id = post_donation(client, make_payload()).json()["id"]
    first = client.post(f"/donations/{donation_id}/claim", json={"claimed_by": "NGO One"})
    second = client.post(f"/donations/{donation_id}/claim", json={"claimed_by": "NGO Two"})
    assert first.status_code == 200
    assert second.status_code == 409
    assert "already been claimed" in second.json()["detail"]
    assert client.get(f"/donations/{donation_id}").json()["claimed_by"] == "NGO One"


def test_claim_missing_donation_is_404(client):
    r = client.post("/donations/42/claim", json={"claimed_by": "Test NGO"})
    assert r.status_code == 404


@pytest.mark.parametrize("body", [{}, {"claimed_by": ""}, {"claimed_by": "   "},
                                  {"claimed_by": "x" * 121}, {"claimed_by": "A", "extra": 1}])
def test_claim_requires_valid_claimer_name(client, make_payload, body):
    donation_id = post_donation(client, make_payload()).json()["id"]
    assert client.post(f"/donations/{donation_id}/claim", json=body).status_code == 422
    assert client.get(f"/donations/{donation_id}").json()["status"] == "available"


def test_expired_donation_cannot_be_claimed(client, make_payload, fake_clock):
    donation_id = post_donation(client, make_payload()).json()["id"]
    fake_clock.advance(hours=3)  # deadline was +2h

    assert client.get(f"/donations/{donation_id}").json()["status"] == "expired"
    assert client.get("/donations", params={"status": "available"}).json() == []
    assert len(client.get("/donations", params={"status": "expired"}).json()) == 1

    r = client.post(f"/donations/{donation_id}/claim", json={"claimed_by": "Late NGO"})
    assert r.status_code == 409
    assert "deadline" in r.json()["detail"]


def test_claimed_donation_stays_claimed_after_deadline(client, make_payload, fake_clock):
    donation_id = post_donation(client, make_payload()).json()["id"]
    client.post(f"/donations/{donation_id}/claim", json={"claimed_by": "Test NGO"})
    fake_clock.advance(hours=5)
    assert client.get(f"/donations/{donation_id}").json()["status"] == "claimed"


def test_concurrent_claims_only_one_wins(db_path, make_payload, fake_clock):
    app = create_app(db_path)
    client = TestClient(app)
    donation_id = post_donation(client, make_payload()).json()["id"]

    results, barrier = [], threading.Barrier(8)

    def worker(n):
        conn = db.connect(db_path)
        try:
            barrier.wait()
            outcome, _ = db.claim_donation(conn, donation_id, f"NGO {n}", fake_clock.now)
            results.append(outcome)
        finally:
            conn.close()

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("claimed") == 1
    assert results.count("already_claimed") == 7


# ---------------------------------------------------- persistence & CORS
def test_data_persists_across_app_instances(db_path, make_payload, fake_clock):
    first = TestClient(create_app(db_path))
    post_donation(first, make_payload(food_name="Persistent soup"))

    second = TestClient(create_app(db_path))  # simulates a server restart
    names = [d["food_name"] for d in second.get("/donations").json()]
    assert names == ["Persistent soup"]


def test_cors_allows_vite_dev_origin(client):
    r = client.options(
        "/donations",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_unknown_origin(client):
    r = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_cors_origins_configurable_via_env(db_path, monkeypatch):
    monkeypatch.setenv("FOODBRIDGE_CORS_ORIGINS", "http://localhost:3000")
    c = TestClient(create_app(db_path))
    r = c.get("/health", headers={"Origin": "http://localhost:3000"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
