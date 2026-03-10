from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models import Activity, RoutePoint
from schemas import AllTracksResponse, RoutePointSchema, RouteResponse, TrackPolyline
from utils.geo import simplify_route

router = APIRouter()


@router.get("/activity/{activity_id}", response_model=RouteResponse)
def get_activity_route(activity_id: int, db: Session = Depends(get_db)):
    activity = db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if not activity.has_gps:
        return RouteResponse(activity_id=activity_id, points=[])

    points = db.scalars(
        select(RoutePoint)
        .where(RoutePoint.activity_id == activity_id)
        .order_by(RoutePoint.sequence)
    ).all()

    return RouteResponse(
        activity_id=activity_id,
        points=[RoutePointSchema.model_validate(p) for p in points],
    )


@router.get("/all-tracks", response_model=AllTracksResponse)
def get_all_tracks(
    bbox: str | None = Query(None, description="south,west,north,east"),
    simplify: bool = True,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    q = select(Activity).where(Activity.has_gps == True)  # noqa: E712

    if year:
        from sqlalchemy import func
        q = q.where(func.strftime("%Y", Activity.start_time) == str(year))

    if bbox:
        try:
            south, west, north, east = [float(v) for v in bbox.split(",")]
            q = q.where(
                Activity.start_lat.between(south, north),
                Activity.start_lng.between(west, east),
            )
        except ValueError:
            pass

    activities = db.scalars(q).all()

    tracks: list[TrackPolyline] = []
    for activity in activities:
        points = db.scalars(
            select(RoutePoint)
            .where(RoutePoint.activity_id == activity.id)
            .order_by(RoutePoint.sequence)
        ).all()

        if not points:
            continue

        coords = [(p.lat, p.lng) for p in points]
        if simplify and len(coords) > 50:
            coords = simplify_route(coords, target_points=50)

        tracks.append(TrackPolyline(
            activity_id=activity.id,
            points=[[lat, lng] for lat, lng in coords],
        ))

    return AllTracksResponse(tracks=tracks)
