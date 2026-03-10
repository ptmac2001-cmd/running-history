from __future__ import annotations
"""Parse Garmin FIT binary files into NormalizedActivity."""
from datetime import datetime, timezone
from pathlib import Path
from ingestion.base import NormalizedActivity, NormalizedRoutePoint, NormalizedLap

# FIT epoch: 1989-12-31 00:00:00 UTC
_FIT_EPOCH_OFFSET = 631065600  # seconds between Unix epoch and FIT epoch
_SEMICIRCLE_FACTOR = 180.0 / (2 ** 31)


def semicircles_to_degrees(value: int) -> float:
    return value * _SEMICIRCLE_FACTOR


def fit_timestamp_to_utc(fit_ts: int) -> datetime:
    return datetime.fromtimestamp(fit_ts + _FIT_EPOCH_OFFSET, tz=timezone.utc).replace(tzinfo=None)


def parse_fit_file(path: Path, source: str) -> NormalizedActivity | None:
    """Parse a single .fit file. Returns NormalizedActivity or None on failure."""
    try:
        import fitparse
    except ImportError:
        raise ImportError("fitparse is required: pip install fitparse")

    fit = fitparse.FitFile(str(path))

    session_data: dict = {}
    route_points: list[NormalizedRoutePoint] = []
    laps: list[NormalizedLap] = []
    lap_number = 0

    for record in fit.get_messages():
        name = record.name

        if name == "session":
            data = {f.name: f.value for f in record.fields}
            session_data = data

        elif name == "lap":
            data = {f.name: f.value for f in record.fields}
            lap_number += 1
            start_time = None
            if data.get("start_time"):
                ts = data["start_time"]
                if isinstance(ts, datetime):
                    start_time = ts.replace(tzinfo=None) if ts.tzinfo else ts
                elif isinstance(ts, (int, float)):
                    start_time = fit_timestamp_to_utc(int(ts))

            duration = None
            if data.get("total_elapsed_time") is not None:
                duration = int(data["total_elapsed_time"])

            distance = None
            if data.get("total_distance") is not None:
                distance = float(data["total_distance"])

            pace = None
            if distance and duration and duration > 0:
                spd = distance / duration
                if spd > 0:
                    pace = 1000 / spd

            laps.append(NormalizedLap(
                lap_number=lap_number,
                start_time=start_time,
                duration_seconds=duration,
                distance_meters=distance,
                avg_pace_sec_per_km=pace,
                avg_heart_rate=data.get("avg_heart_rate"),
                elevation_gain_m=data.get("total_ascent"),
                trigger=str(data.get("lap_trigger", "")).lower() or None,
            ))

        elif name == "record":
            data = {f.name: f.value for f in record.fields}

            lat = data.get("position_lat")
            lng = data.get("position_long")
            if lat is not None and lng is not None:
                lat = semicircles_to_degrees(lat)
                lng = semicircles_to_degrees(lng)

            ts = data.get("timestamp")
            if isinstance(ts, datetime):
                ts = ts.replace(tzinfo=None) if ts.tzinfo else ts
            elif isinstance(ts, (int, float)):
                ts = fit_timestamp_to_utc(int(ts))
            else:
                ts = None

            speed = data.get("speed")  # m/s

            hr = data.get("heart_rate")
            cadence = data.get("cadence")
            if cadence is not None:
                cadence = cadence * 2  # FIT stores running cadence as steps/min per foot

            route_points.append(NormalizedRoutePoint(
                sequence=len(route_points),
                lat=lat if lat is not None else 0.0,
                lng=lng if lng is not None else 0.0,
                elevation_m=data.get("altitude"),
                timestamp=ts,
                heart_rate=int(hr) if hr is not None else None,
                cadence=int(cadence) if cadence is not None else None,
                speed_mps=float(speed) if speed is not None else None,
                distance_m=data.get("distance"),
            ))

    # Filter out points with no valid coordinates
    route_points = [p for p in route_points if p.lat != 0.0 or p.lng != 0.0]

    if not session_data:
        return None

    # Parse start time
    start_time = session_data.get("start_time")
    if isinstance(start_time, datetime):
        start_time = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
    elif isinstance(start_time, (int, float)):
        start_time = fit_timestamp_to_utc(int(start_time))
    else:
        return None

    duration = int(session_data.get("total_elapsed_time") or 0)
    distance = float(session_data.get("total_distance") or 0)

    if distance == 0:
        return None

    sport = str(session_data.get("sport", "running")).lower()
    activity_type = "run"
    if sport in ("cycling", "biking"):
        activity_type = "cycling"
    elif sport == "swimming":
        activity_type = "swimming"

    avg_speed = session_data.get("avg_speed")
    max_speed = session_data.get("max_speed")

    activity = NormalizedActivity(
        source=source,
        start_time=start_time,
        duration_seconds=duration,
        distance_meters=distance,
        activity_type=activity_type,
        moving_time_seconds=int(session_data.get("total_moving_time") or duration),
        elevation_gain_meters=session_data.get("total_ascent"),
        elevation_loss_meters=session_data.get("total_descent"),
        avg_speed_mps=float(avg_speed) if avg_speed else None,
        max_speed_mps=float(max_speed) if max_speed else None,
        avg_heart_rate=session_data.get("avg_heart_rate"),
        max_heart_rate=session_data.get("max_heart_rate"),
        avg_cadence=int(session_data.get("avg_running_cadence", 0) or 0) * 2 or None,
        calories=session_data.get("total_calories"),
        raw_file_path=str(path),
        route_points=route_points,
        laps=laps,
    )
    return activity
