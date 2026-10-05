"""Wedding content: the couple and their events.

Lives in code (not env vars) because it's content - not secret, not per-environment.
Add an event = add an Event + a theme folder (templates/themes/<x>/page.html + css).
"""
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from urllib.parse import quote_plus


def _ordinal(n: int) -> str:
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


@dataclass(frozen=True)
class Person:
    name: str
    nickname: str
    father: str
    relation: str  # "Son" / "Daughter"

    @property
    def parents(self) -> str:
        return f"Mr. & Mrs. {self.father}"

    @property
    def parent_line(self) -> str:
        return f"{self.relation} of {self.parents}"


@dataclass(frozen=True)
class Quote:
    arabic: str
    english: str
    reference: str


@dataclass(frozen=True)
class Event:
    slug: str
    theme: str
    title: str
    welcome_text: str
    date_iso: str  # single source of truth for date+time; keep the UTC offset for guests abroad
    venue_name: str
    venue_address: str
    city: str
    quote: Quote

    @cached_property
    def when(self) -> datetime:
        return datetime.fromisoformat(self.date_iso)

    @property
    def day_ordinal(self) -> str:
        return _ordinal(self.when.day)

    @property
    def date_display(self) -> str:
        return f"{self.when:%A}, {self.day_ordinal} {self.when:%B %Y}"

    @property
    def time_display(self) -> str:
        return f"{self.when:%I:%M %p}".lstrip("0") + " onwards"

    @property
    def _map_query(self) -> str:
        return quote_plus(f"{self.venue_name}, {self.venue_address}")

    @property
    def map_embed_url(self) -> str:
        return f"https://maps.google.com/maps?q={self._map_query}&output=embed"

    @property
    def map_link_url(self) -> str:
        return f"https://www.google.com/maps/search/?api=1&query={self._map_query}"


GROOM = Person("Moinuddin", "Haris", father="Raziuddin", relation="Son")
BRIDE = Person("Meher", "Mehreen", father="Saiful Islam", relation="Daughter")

# The Prophetic dua for newlyweds - shown on every invitation.
WEDDING_DUA = Quote(
    arabic="بَارَكَ اللَّهُ لَكُمَا وَبَارَكَ عَلَيْكُمَا وَجَمَعَ بَيْنَكُمَا فِي خَيْرٍ",
    english="May Allah bless you both, shower His blessings upon you, and unite you in goodness.",
    reference="Sunan Abi Dawud · 2130",
)

NIKAH = Event(
    slug="nikah",
    theme="nikah",
    title="Nikah Ceremony",
    welcome_text=(
        "With the blessings of Allah (Subhanahu wa Ta'ala) and the duas of our elders, "
        "we joyfully invite you and your family to share in the happiness of the sacred union of"
    ),
    date_iso="2026-11-21T19:00:00+05:30",
    venue_name="St. Mary College Hall",
    venue_address="Kalina Church, Kalina Kurla Road, Santacruz East, Mumbai, India",
    city="Mumbai",
    quote=Quote(
        arabic="وَمِنْ آيَاتِهِ أَنْ خَلَقَ لَكُم مِّنْ أَنفُسِكُمْ أَزْوَاجًا لِّتَسْكُنُوا إِلَيْهَا وَجَعَلَ بَيْنَكُم مَّوَدَّةً وَرَحْمَةً",
        english=(
            "And among His signs is that He created for you from yourselves mates that you may "
            "find tranquillity in them; and He placed between you affection and mercy."
        ),
        reference="Surah Ar-Rum · 30:21",
    ),
)

VALIMA = Event(
    slug="valima",
    theme="valima",
    title="Valima Reception",
    welcome_text=(
        "By the grace of Allah (Subhanahu wa Ta'ala), following the Sunnah of the Valima, "
        "we request the pleasure of your company at the reception celebrating the marriage of"
    ),
    date_iso="2026-11-27T20:00:00+05:30",  # TODO: confirm actual Valima time
    venue_name="Meridian Function Hall",
    venue_address="Near Bibi Cancer Hospital, New Malakpet, Hyderabad, Telangana, India",
    city="Hyderabad",
    quote=Quote(
        arabic="رَبَّنَا هَبْ لَنَا مِنْ أَزْوَاجِنَا وَذُرِّيَّاتِنَا قُرَّةَ أَعْيُنٍ وَاجْعَلْنَا لِلْمُتَّقِينَ إِمَامًا",
        english=(
            "Our Lord, grant us from among our spouses and offspring comfort to our eyes, "
            "and make us an example for the righteous."
        ),
        reference="Surah Al-Furqan · 25:74",
    ),
)

EVENTS: dict[str, Event] = {e.slug: e for e in (NIKAH, VALIMA)}
DEFAULT_EVENT = NIKAH.slug
