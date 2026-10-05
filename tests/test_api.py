"""API tests - isolated SQLite DB, reset per test."""
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


def _rows() -> list[Rsvp]:
    with SessionLocal() as db:
        return db.query(Rsvp).all()


def test_root_redirects_to_nikah(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/nikah"


@pytest.mark.parametrize(
    "slug, needles",
    [
        ("nikah", ["theme-nikah", "nk-card", "St. Mary College Hall", "Ar-Rum", "Raziuddin", "Saiful Islam", "7:00 PM"]),
        ("valima", ["theme-valima", "vl-hero", "Meridian Function Hall", "Al-Furqan", "Malakpet", "Hyderabad", "8:00 PM"]),
    ],
)
def test_event_pages(client, slug, needles):
    html = client.get(f"/{slug}").text
    for needle in ["Moinuddin", "Haris", "Meher", "Mehreen", "maps.google.com", f"/{slug}/rsvp", *needles]:
        assert needle in html, needle


def test_unknown_event_404(client):
    assert client.get("/birthday").status_code == 404
    assert client.post("/birthday/rsvp", data={"full_name": "X", "attending": "yes"}).status_code == 404


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_rsvp_tagged_with_event(client):
    client.post("/nikah/rsvp", data={"full_name": "Ali Khan", "attending": "yes", "guest_count": "3"})
    r = client.post("/valima/rsvp", data={"full_name": "Ali Khan", "attending": "yes", "guest_count": "2"})
    assert "JazakAllah" in r.text
    assert sorted((x.event, x.guest_count) for x in _rows()) == [("nikah", 3), ("valima", 2)]


def test_rsvp_declining_forces_zero_guests(client):
    client.post("/valima/rsvp", data={"full_name": "Sara", "attending": "no", "guest_count": "4"})
    [row] = _rows()
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
    r = client.post("/nikah/rsvp", data=data)
    assert r.status_code == 422 and "Please check the form" in r.text
    assert _rows() == []


def test_nikah_has_no_lanterns_or_petals(client):
    html = client.get("/nikah").text
    assert "lantern" not in html and "petal" not in html


def test_date_derived_from_iso():
    from app.events import NIKAH, VALIMA
    assert NIKAH.date_display == "Saturday, 21st November 2026"
    assert VALIMA.time_display == "8:00 PM onwards"
