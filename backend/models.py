from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index,
    Integer, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String)
    activity_type: Mapped[str] = mapped_column(String, nullable=False, default="run")

    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    moving_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    distance_miles: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_gain_feet: Mapped[Optional[float]] = mapped_column(Float)
    elevation_loss_feet: Mapped[Optional[float]] = mapped_column(Float)

    avg_pace_sec_per_mile: Mapped[Optional[float]] = mapped_column(Float)
    avg_speed_mph: Mapped[Optional[float]] = mapped_column(Float)
    max_speed_mph: Mapped[Optional[float]] = mapped_column(Float)

    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    avg_cadence: Mapped[Optional[int]] = mapped_column(Integer)
    calories: Mapped[Optional[int]] = mapped_column(Integer)

    start_lat: Mapped[Optional[float]] = mapped_column(Float)
    start_lng: Mapped[Optional[float]] = mapped_column(Float)
    end_lat: Mapped[Optional[float]] = mapped_column(Float)
    end_lng: Mapped[Optional[float]] = mapped_column(Float)
    bounding_box_json: Mapped[Optional[str]] = mapped_column(Text)

    has_gps: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    gear_name: Mapped[Optional[str]] = mapped_column(String)
    raw_file_path: Mapped[Optional[str]] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    route_points: Mapped[List["RoutePoint"]] = relationship(
        "RoutePoint", back_populates="activity", cascade="all, delete-orphan", lazy="noload"
    )
    laps: Mapped[List["Lap"]] = relationship(
        "Lap", back_populates="activity", cascade="all, delete-orphan", lazy="noload"
    )

    __table_args__ = (
        Index("ix_activities_start_time", "start_time"),
        Index("ix_activities_source", "source"),
        Index("ix_activities_activity_type", "activity_type"),
        Index("ix_activities_distance", "distance_miles"),
    )


class RoutePoint(Base):
    __tablename__ = "route_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_ft: Mapped[Optional[float]] = mapped_column(Float)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    cadence: Mapped[Optional[int]] = mapped_column(Integer)
    speed_mph: Mapped[Optional[float]] = mapped_column(Float)
    distance_mi: Mapped[Optional[float]] = mapped_column(Float)

    activity: Mapped["Activity"] = relationship("Activity", back_populates="route_points")

    __table_args__ = (
        Index("ix_route_points_activity_seq", "activity_id", "sequence"),
    )


class Lap(Base):
    __tablename__ = "laps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    distance_miles: Mapped[Optional[float]] = mapped_column(Float)
    avg_pace_sec_per_mile: Mapped[Optional[float]] = mapped_column(Float)
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    elevation_gain_ft: Mapped[Optional[float]] = mapped_column(Float)
    trigger: Mapped[Optional[str]] = mapped_column(String)

    activity: Mapped["Activity"] = relationship("Activity", back_populates="laps")


class PersonalRecord(Base):
    __tablename__ = "personal_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    distance_key: Mapped[str] = mapped_column(String, nullable=False)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id"), nullable=False)
    time_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    set_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (UniqueConstraint("distance_key", name="uq_pr_distance_key"),)


class ImportLog(Base):
    __tablename__ = "import_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String)
    external_id: Mapped[Optional[str]] = mapped_column(String)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    activity_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("activities.id"))
    status: Mapped[str] = mapped_column(String, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False)  # Unix timestamp
    athlete_id: Mapped[Optional[int]] = mapped_column(Integer)
    athlete_name: Mapped[Optional[str]] = mapped_column(String)
