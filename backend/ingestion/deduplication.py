from __future__ import annotations
"""Duplicate detection before inserting activities."""
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Activity, ImportLog
from ingestion.base import NormalizedActivity

_TIME_WINDOW_SECONDS = 120  # ±2 minutes
_DISTANCE_TOLERANCE = 0.02  # ±2%

# Unit conversion constants
M_TO_MI = 0.000621371
M_TO_FT = 3.28084
MPS_TO_MPH = 2.23694
SEC_PER_KM_TO_SEC_PER_MI = 1.60934


def find_duplicate(activity: NormalizedActivity, db: Session) -> Activity | None:
    """Return existing Activity if this one is a duplicate, else None."""
    window_start = activity.start_time - timedelta(seconds=_TIME_WINDOW_SECONDS)
    window_end = activity.start_time + timedelta(seconds=_TIME_WINDOW_SECONDS)

    candidates = (
        db.query(Activity)
        .filter(Activity.start_time.between(window_start, window_end))
        .all()
    )

    dist_miles = activity.distance_meters * M_TO_MI
    for candidate in candidates:
        dist_diff = abs(candidate.distance_miles - dist_miles)
        dist_rel = dist_diff / max(dist_miles, 0.001)
        if dist_rel <= _DISTANCE_TOLERANCE:
            return candidate

    return None


def insert_activity(activity: NormalizedActivity, db: Session) -> tuple[Activity | None, str]:
    """
    Insert activity if not duplicate.
    Returns (Activity, status) where status is 'ok' or 'duplicate'.
    """
    activity.derive_computed_fields()

    duplicate = find_duplicate(activity, db)
    if duplicate:
        _log(db, activity, status="duplicate", activity_id=duplicate.id)
        return None, "duplicate"

    bounding_box = None
    if activity.route_points:
        lats = [p.lat for p in activity.route_points]
        lngs = [p.lng for p in activity.route_points]
        bounding_box = json.dumps({
            "north": max(lats), "south": min(lats),
            "east": max(lngs), "west": min(lngs),
        })

    from models import RoutePoint, Lap
    db_activity = Activity(
        external_id=activity.external_id,
        source=activity.source,
        title=activity.title,
        activity_type=activity.activity_type,
        start_time=activity.start_time,
        duration_seconds=activity.duration_seconds,
        moving_time_seconds=activity.moving_time_seconds,
        distance_miles=activity.distance_meters * M_TO_MI,
        elevation_gain_feet=activity.elevation_gain_meters * M_TO_FT if activity.elevation_gain_meters is not None else None,
        elevation_loss_feet=activity.elevation_loss_meters * M_TO_FT if activity.elevation_loss_meters is not None else None,
        avg_pace_sec_per_mile=activity.avg_pace_sec_per_km * SEC_PER_KM_TO_SEC_PER_MI if activity.avg_pace_sec_per_km is not None else None,
        avg_speed_mph=activity.avg_speed_mps * MPS_TO_MPH if activity.avg_speed_mps is not None else None,
        max_speed_mph=activity.max_speed_mps * MPS_TO_MPH if activity.max_speed_mps is not None else None,
        avg_heart_rate=activity.avg_heart_rate,
        max_heart_rate=activity.max_heart_rate,
        avg_cadence=activity.avg_cadence,
        calories=activity.calories,
        start_lat=activity.start_lat,
        start_lng=activity.start_lng,
        end_lat=activity.end_lat,
        end_lng=activity.end_lng,
        bounding_box_json=bounding_box,
        has_gps=activity.has_gps,
        notes=activity.notes,
        gear_name=activity.gear_name,
        raw_file_path=activity.raw_file_path,
    )
    db.add(db_activity)
    db.flush()  # get db_activity.id

    for pt in activity.route_points:
        db.add(RoutePoint(
            activity_id=db_activity.id,
            sequence=pt.sequence,
            lat=pt.lat,
            lng=pt.lng,
            elevation_ft=pt.elevation_m * M_TO_FT if pt.elevation_m is not None else None,
            timestamp=pt.timestamp,
            heart_rate=pt.heart_rate,
            cadence=pt.cadence,
            speed_mph=pt.speed_mps * MPS_TO_MPH if pt.speed_mps is not None else None,
            distance_mi=pt.distance_m * M_TO_MI if pt.distance_m is not None else None,
        ))

    for lap in activity.laps:
        db.add(Lap(
            activity_id=db_activity.id,
            lap_number=lap.lap_number,
            start_time=lap.start_time,
            duration_seconds=lap.duration_seconds,
            distance_miles=lap.distance_meters * M_TO_MI if lap.distance_meters is not None else None,
            avg_pace_sec_per_mile=lap.avg_pace_sec_per_km * SEC_PER_KM_TO_SEC_PER_MI if lap.avg_pace_sec_per_km is not None else None,
            avg_heart_rate=lap.avg_heart_rate,
            elevation_gain_ft=lap.elevation_gain_m * M_TO_FT if lap.elevation_gain_m is not None else None,
            trigger=lap.trigger,
        ))

    db.commit()
    _log(db, activity, status="ok", activity_id=db_activity.id)
    return db_activity, "ok"


def _log(db: Session, activity: NormalizedActivity, status: str, activity_id: int | None = None) -> None:
    db.add(ImportLog(
        source=activity.source,
        file_path=activity.raw_file_path,
        external_id=activity.external_id,
        activity_id=activity_id,
        status=status,
    ))
    db.commit()
