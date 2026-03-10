from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from database import get_db
from models import Activity, Lap
from schemas import ActivityDetail, ActivityListResponse, ActivitySummary, LapSchema

router = APIRouter()


@router.get("", response_model=ActivityListResponse)
def list_activities(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    year: int | None = None,
    month: int | None = None,
    source: str | None = None,
    activity_type: str | None = None,
    min_distance_mi: float | None = None,
    max_distance_mi: float | None = None,
    sort: str = "start_time",
    order: str = "desc",
    db: Session = Depends(get_db),
):
    q = select(Activity)

    if year:
        q = q.where(func.strftime("%Y", Activity.start_time) == str(year))
    if month:
        q = q.where(func.strftime("%m", Activity.start_time) == f"{month:02d}")
    if source:
        q = q.where(Activity.source == source)
    if activity_type:
        q = q.where(Activity.activity_type == activity_type)
    if min_distance_mi is not None:
        q = q.where(Activity.distance_miles >= min_distance_mi)
    if max_distance_mi is not None:
        q = q.where(Activity.distance_miles <= max_distance_mi)

    # Count total
    count_q = select(func.count()).select_from(q.subquery())
    total = db.scalar(count_q)

    # Sort
    sort_col = getattr(Activity, sort, Activity.start_time)
    if order == "desc":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())

    q = q.offset((page - 1) * limit).limit(limit)
    activities = db.scalars(q).all()

    return ActivityListResponse(
        items=[ActivitySummary.model_validate(a) for a in activities],
        total=total or 0,
        page=page,
        limit=limit,
    )


@router.get("/{activity_id}", response_model=ActivityDetail)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    laps = db.scalars(
        select(Lap).where(Lap.activity_id == activity_id).order_by(Lap.lap_number)
    ).all()

    detail = ActivityDetail.model_validate(activity)
    detail.laps = [LapSchema.model_validate(lap) for lap in laps]
    return detail


@router.delete("/{activity_id}")
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    db.delete(activity)
    db.commit()
    return {"success": True}
