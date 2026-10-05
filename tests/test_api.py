"""API tests - each test gets an isolated SQLite DB."""
import os
import tempfile

import pytest

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Rsvp  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


def _count() -> int:
    with SessionLocal() as db:
        return db.query(Rsvp).count()


def test_homepage_has_couple_and_map(client):
    html = client.get("/").text
    for needle in ("Moinuddin", "Haris", "Meher", "Mehreen", "maps.google.com", "Ar-Rum"):
        assert needle in html


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_rsvp_attending_saved(client):
    r = client.post("/rsvp", data={"full_name": "Ali Khan", "attending": "yes", "guest_count": "3"})
    assert r.status_code == 200
    assert "JazakAllah" in r.text
    assert _count() == 1


def test_rsvp_declining_forces_zero_guests(client):
    client.post("/rsvp", data={"full_name": "Sara", "attending": "no", "guest_count": "4"})
    with SessionLocal() as db:
        row = db.query(Rsvp).one()
    assert row.attending is False and row.guest_count == 0


@pytest.mark.parametrize(
    "data",
    [
        {"full_name": "", "attending": "yes"},
        {"full_name": "Zaid"},
        {"full_name": "Zaid", "attending": "yes", "email": "not-an-email"},
    ],
)
def test_rsvp_validation(client, data):
    r = client.post("/rsvp", data=data)
    assert r.status_code == 422
    assert "Please check the form" in r.text
    assert _count() == 0
