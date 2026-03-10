from __future__ import annotations
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{BASE_DIR}/data/running_history.db"
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:8000/auth/strava/callback"
    garmin_email: str = ""
    garmin_password: str = ""

    model_config = {"env_file": BASE_DIR / ".env", "extra": "ignore"}


settings = Settings()
