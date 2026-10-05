"""FastAPI entrypoint for the wedding invitation."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from urllib.parse import quote_plus

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import Base, engine, get_db
from app.models import Rsvp
from app.schemas import RsvpIn

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Prototype convenience; swap for Alembic migrations once schema settles.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Haris & Mehreen - Wedding Invitation", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbDep = Annotated[Session, Depends(get_db)]


@app.get("/", response_class=HTMLResponse)
def invitation(request: Request, settings: SettingsDep):
    q = quote_plus(settings.map_query)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "s": settings,
            "map_embed_url": f"https://maps.google.com/maps?q={q}&output=embed",
            "map_link_url": f"https://www.google.com/maps/search/?api=1&query={q}",
        },
    )


@app.post("/rsvp", response_class=HTMLResponse)
def submit_rsvp(
    request: Request,
    db: DbDep,
    full_name: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    phone: Annotated[str, Form()] = "",
    attending: Annotated[str, Form()] = "",
    guest_count: Annotated[int, Form()] = 1,
    message: Annotated[str, Form()] = "",
):
    try:
        data = RsvpIn(
            full_name=full_name,
            email=email,
            phone=phone,
            attending=attending == "yes",
            guest_count=guest_count if attending == "yes" else 0,
            message=message,
        )
        if attending not in {"yes", "no"}:
            raise ValueError("Please tell us whether you can attend.")
    except (ValidationError, ValueError) as exc:
        errors = (
            [f"{e['loc'][0].replace('_', ' ').title()}: {e['msg']}" for e in exc.errors()]
            if isinstance(exc, ValidationError)
            else [str(exc)]
        )
        return templates.TemplateResponse(
            request, "partials/rsvp_error.html", {"errors": errors}, status_code=422
        )

    db.add(Rsvp(**data.model_dump()))
    db.commit()
    return templates.TemplateResponse(
        request, "partials/rsvp_thanks.html", {"rsvp": data}
    )


@app.get("/health")
def health(db: DbDep):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
