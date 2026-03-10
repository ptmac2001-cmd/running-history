"""Strava incremental sync."""
from __future__ import annotations
import time
from datetime import datetime, timedelta

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Activity, OAuthToken
from ingestion.base import NormalizedActivity, NormalizedRoutePoint
from ingestion.deduplication import insert_activity

router = APIRouter()

_STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
_STRAVA_API = "https://www.strava.com/api/v3"

_RUN_TYPES = {"run", "trail run", "treadmill", "virtualrun", "race"}


def _get_access_token(db: Session) -> str:
    token = db.query(OAuthToken).filter_by(provider="strava").first()
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Strava not connected. Visit /auth/strava to authorize.",
        )
    if token.expires_at < time.time() + 60:
        resp = requests.post(_STRAVA_TOKEN_URL, data={
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "refresh_token": token.refresh_token,
            "grant_type": "refresh_token",
        }, timeout=10)
        resp.raise_for_status()
        refreshed = resp.json()
        token.access_token = refreshed["access_token"]
        token.refresh_token = refreshed["refresh_token"]
        token.expires_at = int(refreshed["expires_at"])
        db.commit()
    return token.access_token


def _strava_get(path: str, access_token: str, **params) -> dict | list:
    resp = requests.get(
        f"{_STRAVA_API}{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


@router.post("/strava")
def sync_strava(db: Session = Depends(get_db)):
    """Fetch new Strava activities since the last sync and insert into DB."""
    access_token = _get_access_token(db)

    latest = (
        db.query(Activity)
        .filter(Activity.source == "strava")
        .order_by(Activity.start_time.desc())
        .first()
    )
    after = int(latest.start_time.timestamp()) if latest else None

    inserted = 0
    duplicates = 0
    errors = 0
    error_messages: list[str] = []

    page = 1
    while True:
        params = {"per_page": 100, "page": page}
        if after:
            params["after"] = after
        activities = _strava_get("/athlete/activities", access_token, **params)
        if not activities:
            break
        for strava_activity in activities:
            try:
                type_str = str(strava_activity.get("sport_type") or strava_activity.get("type") or "").lower()
                if "run" not in type_str:
                    continue
                activity = _normalize(strava_activity, access_token)
                _, status = insert_activity(activity, db)
                if status == "ok":
                    inserted += 1
                else:
                    duplicates += 1
            except Exception as e:
                errors += 1
                error_messages.append(f"{strava_activity.get('id')}: {e}")
        page += 1

    return {
        "inserted": inserted,
        "duplicates": duplicates,
        "errors": errors,
        "error_messages": error_messages[:10],
    }


def _normalize(a: dict, access_token: str) -> NormalizedActivity:
    type_str = str(a.get("sport_type") or a.get("type") or "").lower()
    if "treadmill" in type_str:
        activity_type = "treadmill"
    elif "trail" in type_str:
        activity_type = "trail_run"
    else:
        activity_type = "run"

    elapsed = a.get("elapsed_time") or 0
    duration_seconds = int(elapsed)

    moving = a.get("moving_time")
    moving_time_seconds = int(moving) if moving else None

    distance_m = float(a.get("distance") or 0)
    elev_gain = float(a["total_elevation_gain"]) if a.get("total_elevation_gain") else None
    avg_hr = int(a["average_heartrate"]) if a.get("average_heartrate") else None
    max_hr = int(a["max_heartrate"]) if a.get("max_heartrate") else None
    avg_cadence = int(a["average_cadence"]) if a.get("average_cadence") else None
    avg_speed = float(a["average_speed"]) if a.get("average_speed") else None
    max_speed = float(a["max_speed"]) if a.get("max_speed") else None

    start_lat = start_lng = end_lat = end_lng = None
    slatlng = a.get("start_latlng")
    if slatlng and len(slatlng) == 2:
        start_lat, start_lng = slatlng
    elatlng = a.get("end_latlng")
    if elatlng and len(elatlng) == 2:
        end_lat, end_lng = elatlng

    gear_name = None
    if a.get("gear_id"):
        try:
            gear = _strava_get(f"/gear/{a['gear_id']}", access_token)
            gear_name = gear.get("name")
        except Exception:
            pass

    start_date = None
    if a.get("start_date"):
        start_date = datetime.fromisoformat(a["start_date"].replace("Z", "+00:00"))

    route_points = _fetch_streams(a["id"], start_date, access_token)

    return NormalizedActivity(
        source="strava",
        external_id=f"strava:{a['id']}",
        title=a.get("name"),
        activity_type=activity_type,
        start_time=start_date,
        duration_seconds=duration_seconds,
        moving_time_seconds=moving_time_seconds,
        distance_meters=distance_m,
        elevation_gain_meters=elev_gain,
        avg_heart_rate=avg_hr,
        max_heart_rate=max_hr,
        avg_cadence=avg_cadence,
        avg_speed_mps=avg_speed,
        max_speed_mps=max_speed,
        start_lat=start_lat,
        start_lng=start_lng,
        end_lat=end_lat,
        end_lng=end_lng,
        gear_name=gear_name,
        route_points=route_points,
    )


def _fetch_streams(activity_id: int, start_date: datetime | None, access_token: str) -> list[NormalizedRoutePoint]:
    try:
        streams = _strava_get(
            f"/activities/{activity_id}/streams",
            access_token,
            keys="latlng,altitude,heartrate,cadence,velocity_smooth,distance,time",
            key_by_type=True,
            resolution="medium",
        )
        latlng_stream = streams.get("latlng")
        if not latlng_stream or not latlng_stream.get("data"):
            return []

        latlng = latlng_stream["data"]
        alt = (streams["altitude"]["data"] if "altitude" in streams else None) or []
        hr = (streams["heartrate"]["data"] if "heartrate" in streams else None) or []
        cad = (streams["cadence"]["data"] if "cadence" in streams else None) or []
        vel = (streams["velocity_smooth"]["data"] if "velocity_smooth" in streams else None) or []
        dist = (streams["distance"]["data"] if "distance" in streams else None) or []
        times = (streams["time"]["data"] if "time" in streams else None) or []

        points = []
        for i, (lat, lng) in enumerate(latlng):
            ts = None
            if start_date and i < len(times):
                ts = start_date + timedelta(seconds=times[i])
            points.append(NormalizedRoutePoint(
                sequence=i,
                lat=lat,
                lng=lng,
                elevation_m=alt[i] if i < len(alt) else None,
                timestamp=ts,
                heart_rate=int(hr[i]) if i < len(hr) and hr[i] is not None else None,
                cadence=int(cad[i]) if i < len(cad) and cad[i] is not None else None,
                speed_mps=vel[i] if i < len(vel) else None,
                distance_m=dist[i] if i < len(dist) else None,
            ))
        return points
    except Exception:
        return []
