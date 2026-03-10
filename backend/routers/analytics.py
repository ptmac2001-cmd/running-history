from __future__ import annotations
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from database import get_db
from models import Activity, PersonalRecord, RoutePoint
from schemas import (
    HRZone, MonthStat, PaceTrendPoint, PersonalRecordSchema,
    SourceStat, StreakInfo, SummaryStats, YearStat,
)
from utils.hr_zones import calculate_zones

router = APIRouter()

# PR distances in miles
PR_DISTANCES = {
    "1k": 0.621371,
    "1mi": 1.0,
    "5k": 3.10686,
    "10k": 6.21371,
    "half": 13.1094,
    "marathon": 26.2188,
}

PR_LABELS = {
    "1k": "1 km",
    "1mi": "1 mile",
    "5k": "5 km",
    "10k": "10 km",
    "half": "Half Marathon",
    "marathon": "Marathon",
}


@router.get("/summary", response_model=SummaryStats)
def get_summary(db: Session = Depends(get_db)):
    row = db.execute(select(
        func.count(Activity.id),
        func.sum(Activity.distance_miles),
        func.sum(Activity.duration_seconds),
        func.sum(Activity.elevation_gain_feet),
    )).one()

    total_runs, total_dist, total_time, total_elev = row

    years = db.scalars(
        select(func.strftime("%Y", Activity.start_time)).distinct()
    ).all()

    sources = db.scalars(
        select(Activity.source).distinct()
    ).all()

    return SummaryStats(
        total_runs=total_runs or 0,
        total_distance_miles=round(total_dist or 0, 2),
        total_time_hours=round((total_time or 0) / 3600, 2),
        total_elevation_ft=round(total_elev or 0, 1),
        years_active=len(years),
        sources=list(set(sources)),
    )


@router.get("/by-year", response_model=list[YearStat])
def get_by_year(db: Session = Depends(get_db)):
    rows = db.execute(select(
        func.strftime("%Y", Activity.start_time).label("year"),
        func.count(Activity.id).label("runs"),
        func.sum(Activity.distance_miles).label("distance"),
        func.avg(Activity.avg_pace_sec_per_mile).label("avg_pace"),
        func.sum(Activity.elevation_gain_feet).label("elevation"),
    ).group_by("year").order_by("year")).all()

    return [
        YearStat(
            year=int(row.year),
            runs=row.runs,
            distance_miles=round(row.distance or 0, 2),
            avg_pace_sec_per_mile=round(row.avg_pace, 1) if row.avg_pace else None,
            elevation_gain_ft=round(row.elevation or 0, 1),
        )
        for row in rows
    ]


@router.get("/by-month", response_model=list[MonthStat])
def get_by_month(year: int | None = None, db: Session = Depends(get_db)):
    q = select(
        func.strftime("%m", Activity.start_time).label("month"),
        func.count(Activity.id).label("runs"),
        func.sum(Activity.distance_miles).label("distance"),
    ).group_by("month").order_by("month")

    if year:
        q = q.where(func.strftime("%Y", Activity.start_time) == str(year))

    rows = db.execute(q).all()
    return [
        MonthStat(
            month=int(row.month),
            runs=row.runs,
            distance_miles=round(row.distance or 0, 2),
        )
        for row in rows
    ]


@router.get("/pace-trend", response_model=list[PaceTrendPoint])
def get_pace_trend(
    period: str = Query("monthly", pattern="^(monthly|yearly)$"),
    years: int = 5,
    db: Session = Depends(get_db),
):
    fmt = "%Y-%m" if period == "monthly" else "%Y"

    q = select(
        func.strftime(fmt, Activity.start_time).label("period"),
        func.avg(Activity.avg_pace_sec_per_mile).label("avg_pace"),
        func.count(Activity.id).label("count"),
    ).where(
        Activity.avg_pace_sec_per_mile.isnot(None)
    ).group_by("period").order_by("period")

    rows = db.execute(q).all()
    return [
        PaceTrendPoint(
            period=row.period,
            avg_pace_sec_per_mile=round(row.avg_pace, 1),
            run_count=row.count,
        )
        for row in rows
        if row.avg_pace
    ]


@router.get("/hr-zones", response_model=list[HRZone])
def get_hr_zones(
    max_hr: int = Query(190, ge=100, le=220),
    db: Session = Depends(get_db),
):
    rows = db.execute(select(
        Activity.avg_heart_rate,
        Activity.duration_seconds,
    ).where(Activity.avg_heart_rate.isnot(None))).all()

    hr_seconds = [(row.avg_heart_rate, row.duration_seconds or 0) for row in rows]
    zones = calculate_zones(hr_seconds, max_hr)

    return [HRZone(**z) for z in zones]


@router.get("/personal-records", response_model=list[PersonalRecordSchema])
def get_personal_records(db: Session = Depends(get_db)):
    records = db.scalars(select(PersonalRecord)).all()
    result = []
    for rec in records:
        label = PR_LABELS.get(rec.distance_key, rec.distance_key)
        secs = rec.time_seconds
        result.append(PersonalRecordSchema(
            distance_key=rec.distance_key,
            label=label,
            time_seconds=secs,
            activity_id=rec.activity_id,
            set_at=rec.set_at,
            formatted_time=_format_time(secs),
        ))
    return result


@router.post("/personal-records/recompute")
def recompute_personal_records(db: Session = Depends(get_db)):
    """Recompute PRs from all activities. Call after importing new data."""
    from models import PersonalRecord

    for key, dist_mi in PR_DISTANCES.items():
        tolerance = dist_mi * 0.05  # 5% tolerance for race distances
        best = db.execute(select(
            Activity.id,
            Activity.duration_seconds,
            Activity.moving_time_seconds,
            Activity.start_time,
        ).where(
            Activity.distance_miles.between(dist_mi - tolerance, dist_mi + tolerance),
            Activity.activity_type.in_(["run", "trail_run", "race"]),
        ).order_by(
            func.coalesce(Activity.moving_time_seconds, Activity.duration_seconds).asc()
        ).limit(1)).one_or_none()

        if not best:
            continue

        time_s = best.moving_time_seconds or best.duration_seconds
        existing = db.scalar(
            select(PersonalRecord).where(PersonalRecord.distance_key == key)
        )
        if existing:
            existing.activity_id = best.id
            existing.time_seconds = time_s
            existing.set_at = best.start_time
        else:
            db.add(PersonalRecord(
                distance_key=key,
                activity_id=best.id,
                time_seconds=time_s,
                set_at=best.start_time,
            ))

    db.commit()
    return {"recomputed": True}


@router.get("/longest-streak", response_model=StreakInfo)
def get_longest_streak(db: Session = Depends(get_db)):
    dates = db.scalars(
        select(func.date(Activity.start_time)).distinct().order_by(func.date(Activity.start_time))
    ).all()

    if not dates:
        return StreakInfo(current_streak_days=0, longest_streak_days=0, longest_streak_start=None)

    date_list = [date.fromisoformat(d) for d in dates]

    longest = 1
    longest_start = date_list[0]
    current = 1
    current_start = date_list[0]

    for i in range(1, len(date_list)):
        if date_list[i] - date_list[i - 1] == timedelta(days=1):
            current += 1
            if current > longest:
                longest = current
                longest_start = current_start
        else:
            current = 1
            current_start = date_list[i]

    today = date.today()
    current_streak = 0
    for d in reversed(date_list):
        if d == today - timedelta(days=current_streak):
            current_streak += 1
        else:
            break

    return StreakInfo(
        current_streak_days=current_streak,
        longest_streak_days=longest,
        longest_streak_start=str(longest_start) if longest_start else None,
    )


@router.get("/sources", response_model=list[SourceStat])
def get_sources(db: Session = Depends(get_db)):
    rows = db.execute(select(
        Activity.source,
        func.count(Activity.id).label("count"),
        func.min(Activity.start_time).label("earliest"),
        func.max(Activity.start_time).label("latest"),
    ).group_by(Activity.source).order_by(func.count(Activity.id).desc())).all()

    return [
        SourceStat(
            source=row.source,
            count=row.count,
            earliest=str(row.earliest)[:10] if row.earliest else None,
            latest=str(row.latest)[:10] if row.latest else None,
        )
        for row in rows
    ]


def _format_time(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
