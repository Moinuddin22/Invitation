"""Validation for incoming RSVP data."""
from pydantic import BaseModel, EmailStr, Field, field_validator


class RsvpIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    attending: bool
    guest_count: int = Field(default=1, ge=0, le=10)
    message: str | None = Field(default=None, max_length=1000)

    @field_validator("email", "phone", "message", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        return v.strip() or None if isinstance(v, str) else v

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()
