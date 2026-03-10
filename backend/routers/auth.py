"""Strava OAuth2 authentication flow."""
import urllib.parse

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import OAuthToken

router = APIRouter()

_STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
_STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"


@router.get("/strava")
def strava_auth():
    """Redirect user to Strava authorization page."""
    if not settings.strava_client_id:
        raise HTTPException(status_code=500, detail="STRAVA_CLIENT_ID not configured")
    params = {
        "client_id": settings.strava_client_id,
        "redirect_uri": settings.strava_redirect_uri,
        "response_type": "code",
        "scope": "activity:read_all",
    }
    url = f"{_STRAVA_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)


@router.get("/strava/callback")
def strava_callback(code: str, db: Session = Depends(get_db)):
    """Handle Strava OAuth callback, store tokens, redirect to frontend."""
    resp = requests.post(_STRAVA_TOKEN_URL, data={
        "client_id": settings.strava_client_id,
        "client_secret": settings.strava_client_secret,
        "code": code,
        "grant_type": "authorization_code",
    }, timeout=10)
    resp.raise_for_status()
    token_response = resp.json()

    athlete = token_response.get("athlete") or {}
    first = athlete.get("firstname", "") or ""
    last = athlete.get("lastname", "") or ""
    athlete_name = f"{first} {last}".strip() or None

    existing = db.query(OAuthToken).filter_by(provider="strava").first()
    if existing:
        existing.access_token = token_response["access_token"]
        existing.refresh_token = token_response["refresh_token"]
        existing.expires_at = int(token_response["expires_at"])
        existing.athlete_id = athlete.get("id")
        existing.athlete_name = athlete_name
    else:
        db.add(OAuthToken(
            provider="strava",
            access_token=token_response["access_token"],
            refresh_token=token_response["refresh_token"],
            expires_at=int(token_response["expires_at"]),
            athlete_id=athlete.get("id"),
            athlete_name=athlete_name,
        ))
    db.commit()

    return RedirectResponse("http://localhost:5173/?strava=connected")


@router.get("/strava/status")
def strava_status(db: Session = Depends(get_db)):
    """Check if Strava is connected."""
    token = db.query(OAuthToken).filter_by(provider="strava").first()
    if not token:
        return {"connected": False}
    return {
        "connected": True,
        "athlete_name": token.athlete_name,
        "athlete_id": token.athlete_id,
    }
