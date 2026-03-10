from __future__ import annotations
"""Base classes and normalized data structures for all importers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class NormalizedRoutePoint:
    sequence: int
    lat: float
    lng: float
    elevation_m: float | None = None
    timestamp: datetime | None = None
    heart_rate: int | None = None
    cadence: int | None = None
    speed_mps: float | None = None
    distance_m: float | None = None


@dataclass
class NormalizedLap:
    lap_number: int
    start_time: datetime | None = None
    duration_seconds: int | None = None
    distance_meters: float | None = None
    avg_pace_sec_per_km: float | None = None
    avg_heart_rate: int | None = None
    elevation_gain_m: float | None = None
    trigger: str | None = None  # manual|distance|time


@dataclass
class NormalizedActivity:
    """All fields in SI units: meters, seconds, m/s, decimal degrees, UTC."""
    source: str
    start_time: datetime  # UTC
    duration_seconds: int
    distance_meters: float

    external_id: str | None = None
    title: str | None = None
    activity_type: str = "run"

    moving_time_seconds: int | None = None
    elevation_gain_meters: float | None = None
    elevation_loss_meters: float | None = None

    avg_pace_sec_per_km: float | None = None
    avg_speed_mps: float | None = None
    max_speed_mps: float | None = None

    avg_heart_rate: int | None = None
    max_heart_rate: int | None = None
    avg_cadence: int | None = None
    calories: int | None = None

    start_lat: float | None = None
    start_lng: float | None = None
    end_lat: float | None = None
    end_lng: float | None = None

    has_gps: bool = False
    notes: str | None = None
    gear_name: str | None = None
    raw_file_path: str | None = None

    route_points: list[NormalizedRoutePoint] = field(default_factory=list)
    laps: list[NormalizedLap] = field(default_factory=list)

    def derive_computed_fields(self) -> None:
        """Compute pace/speed and bounding box from route points if not already set."""
        if self.distance_meters > 0 and self.duration_seconds > 0:
            if self.avg_speed_mps is None:
                self.avg_speed_mps = self.distance_meters / self.duration_seconds
            if self.avg_pace_sec_per_km is None and self.avg_speed_mps > 0:
                self.avg_pace_sec_per_km = 1000 / self.avg_speed_mps

        if self.route_points:
            self.has_gps = True
            lats = [p.lat for p in self.route_points]
            lngs = [p.lng for p in self.route_points]
            self.start_lat = self.route_points[0].lat
            self.start_lng = self.route_points[0].lng
            self.end_lat = self.route_points[-1].lat
            self.end_lng = self.route_points[-1].lng


@dataclass
class ImportResult:
    source: str
    total: int = 0
    inserted: int = 0
    duplicates: int = 0
    errors: int = 0
    error_messages: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"[{self.source}] total={self.total} inserted={self.inserted} "
            f"duplicates={self.duplicates} errors={self.errors}"
        )


class BaseImporter(ABC):
    source_name: str = ""

    @abstractmethod
    def run(self, data_dir: Path, db_session) -> ImportResult:
        """Import all data from data_dir into the database."""
        ...
