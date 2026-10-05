"""Central configuration. One source of truth for wedding details & settings."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Infra
    database_url: str = "sqlite:///./invitation.db"

    # Couple
    groom_name: str = "Moinuddin"
    groom_nickname: str = "Haris"
    bride_name: str = "Meher"
    bride_nickname: str = "Mehreen"

    # Event (placeholders - override via env vars)
    wedding_date_display: str = "Saturday, 12th December 2026"
    wedding_date_iso: str = "2026-12-12T19:00:00"
    wedding_time_display: str = "7:00 PM onwards"
    venue_name: str = "Grand Celebration Hall"
    venue_address: str = "Banjara Hills, Hyderabad, Telangana, India"

    @property
    def map_query(self) -> str:
        return f"{self.venue_name}, {self.venue_address}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
