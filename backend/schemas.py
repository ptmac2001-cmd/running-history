from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RoutePointSchema(BaseModel):
    sequence: int
    lat: float
    lng: float
    elevation_ft: float | None = None
    heart_rate: int | None = None
    cadence: int | None = None
    speed_mph: float | None = None
    distance_mi: float | None = None


class LapSchema(BaseModel):
    lap_number: int
    duration_seconds: int | None = None
    distance_miles: float | None = None
    avg_pace_sec_per_mile: float | None = None
    avg_heart_rate: int | None = None
    elevation_gain_ft: float | None = None


class ActivitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    title: str | None
    activity_type: str
    start_time: datetime
    duration_seconds: int
    distance_miles: float
    elevation_gain_feet: float | None
    avg_pace_sec_per_mile: float | None
    avg_heart_rate: int | None
    calories: int | None
    has_gps: bool
    start_lat: float | None
    start_lng: float | None


class ActivityDetail(ActivitySummary):
    moving_time_seconds: int | None
    elevation_loss_feet: float | None
    avg_speed_mph: float | None
    max_speed_mph: float | None
    max_heart_rate: int | None
    avg_cadence: int | None
    end_lat: float | None
    end_lng: float | None
    notes: str | None
    gear_name: str | None
    laps: list[LapSchema] = []


class ActivityListResponse(BaseModel):
    items: list[ActivitySummary]
    total: int
    page: int
    limit: int


class RouteResponse(BaseModel):
    activity_id: int
    points: list[RoutePointSchema]


class TrackPolyline(BaseModel):
    activity_id: int
    points: list[list[float]]  # [[lat, lng], ...]


class AllTracksResponse(BaseModel):
    tracks: list[TrackPolyline]


class YearStat(BaseModel):
    year: int
    runs: int
    distance_miles: float
    avg_pace_sec_per_mile: float | None
    elevation_gain_ft: float | None


class MonthStat(BaseModel):
    month: int
    runs: int
    distance_miles: float


class PaceTrendPoint(BaseModel):
    period: str
    avg_pace_sec_per_mile: float
    run_count: int


class HRZone(BaseModel):
    zone: int
    label: str
    seconds: int
    percentage: float


class PersonalRecordSchema(BaseModel):
    distance_key: str
    label: str
    time_seconds: int
    activity_id: int
    set_at: datetime
    formatted_time: str


class StreakInfo(BaseModel):
    current_streak_days: int
    longest_streak_days: int
    longest_streak_start: str | None


class SourceStat(BaseModel):
    source: str
    count: int
    earliest: str | None
    latest: str | None


class SummaryStats(BaseModel):
    total_runs: int
    total_distance_miles: float
    total_time_hours: float
    total_elevation_ft: float
    years_active: int
    sources: list[str]
