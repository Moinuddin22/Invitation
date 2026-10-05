"""FastAPI entrypoint: one app, one DB, one link per event (/nikah, /valima)."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app.events import BRIDE, DEFAULT_EVENT, EVENTS, GROOM, WEDDING_DUA, Event
from app.models import Rsvp
from app.schemas import RsvpIn

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Prototype convenience; swap for Alembic migrations once schema settles.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Haris & Mehreen - Wedding Invitations", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals.update(groom=GROOM, bride=BRIDE, dua=WEDDING_DUA)


def get_event(slug: str) -> Event:
    if slug not in EVENTS:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return EVENTS[slug]


EventDep = Annotated[Event, Depends(get_event)]
DbDep = Annotated[Session, Depends(get_db)]


# Fixed paths first - /{slug} would otherwise swallow them.
@app.get("/health")
def health(db: DbDep):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/")
def root():
    return RedirectResponse(f"/{DEFAULT_EVENT}")


@app.get("/{slug}", response_class=HTMLResponse)
def invitation(request: Request, event: EventDep):
    # Each theme owns its full page layout; only components are shared.
    return templates.TemplateResponse(request, f"themes/{event.theme}/page.html", {"e": event})


@app.post("/{slug}/rsvp", response_class=HTMLResponse)
def submit_rsvp(
    request: Request,
    event: EventDep,
    db: DbDep,
    full_name: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    phone: Annotated[str, Form()] = "",
    attending: Annotated[str, Form()] = "",
    guest_count: Annotated[int, Form()] = 1,
    message: Annotated[str, Form()] = "",
):
    try:
        if attending not in {"yes", "no"}:
            raise ValueError("Please tell us whether you can attend.")
        data = RsvpIn(
            full_name=full_name,
            email=email,
            phone=phone,
            attending=attending == "yes",
            guest_count=guest_count if attending == "yes" else 0,
            message=message,
        )
    except (ValidationError, ValueError) as exc:
        errors = (
            [f"{e['loc'][0].replace('_', ' ').title()}: {e['msg']}" for e in exc.errors()]
            if isinstance(exc, ValidationError)
            else [str(exc)]
        )
        return templates.TemplateResponse(
            request, "partials/rsvp_error.html", {"errors": errors}, status_code=422
        )

    db.add(Rsvp(event=event.slug, **data.model_dump()))
    db.commit()
    return templates.TemplateResponse(request, "partials/rsvp_thanks.html", {"rsvp": data})
