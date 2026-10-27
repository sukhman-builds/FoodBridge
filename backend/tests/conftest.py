from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import clock
from app.main import create_app

START = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self):
        self.now = START

    def advance(self, **kwargs):
        self.now += timedelta(**kwargs)


@pytest.fixture
def fake_clock(monkeypatch):
    fc = FakeClock()
    monkeypatch.setattr(clock, "utcnow", lambda: fc.now)
    return fc


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def client(db_path, fake_clock):
    return TestClient(create_app(db_path))


@pytest.fixture
def make_payload(fake_clock):
    def _make(**overrides):
        payload = {
            "food_name": "Vegetable biryani",
            "description": "Cooked this evening, packed in sealed trays.",
            "servings": 40,
            "location": "12 Example Street, Sample Town",
            "pickup_deadline": (fake_clock.now + timedelta(hours=2)).isoformat(),
            "donor_name": "Test Kitchen",
            "donor_contact": "donor@example.com",
            "category": "Prepared Meals",
        }
        payload.update(overrides)
        return payload

    return _make
