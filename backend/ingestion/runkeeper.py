from __future__ import annotations
"""Runkeeper importer — CSV + GPX export."""
import csv
import zipfile
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from sqlalchemy.orm import Session
from ingestion.base import BaseImporter, ImportResult
from ingestion.deduplication import insert_activity
from utils.gpx_parser import parse_gpx_file


class RunkeeperImporter(BaseImporter):
    source_name = "runkeeper"

    def run(self, data_dir: Path, db: Session) -> ImportResult:
        result = ImportResult(source=self.source_name)

        # Extract zip if present
        for item in data_dir.iterdir():
            if item.suffix.lower() == ".zip":
                with zipfile.ZipFile(item) as zf:
                    zf.extractall(data_dir / "extracted")

        # Find the CSV
        csv_files = list(data_dir.rglob("cardioActivities.csv"))
        if not csv_files:
            print(f"[runkeeper] No cardioActivities.csv found in {data_dir}")
            return result

        csv_path = csv_files[0]
        csv_dir = csv_path.parent

        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        result.total = len(rows)

        for row in tqdm(rows, desc="Runkeeper activities"):
            try:
                activity = _parse_row(row, csv_dir, self.source_name)
                if activity is None:
                    result.errors += 1
                    continue
                _, status = insert_activity(activity, db)
                if status == "ok":
                    result.inserted += 1
                elif status == "duplicate":
                    result.duplicates += 1
            except Exception as e:
                result.errors += 1
                result.error_messages.append(f"{row.get('Date', '?')}: {e}")

        return result


def _parse_duration(duration_str: str) -> int | None:
    """Parse 'H:MM:SS' or 'MM:SS' duration string to seconds."""
    if not duration_str:
        return None
    parts = duration_str.strip().split(":")
    try:
        parts = [int(p) for p in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
    except ValueError:
        pass
    return None


_RUNKEEPER_TYPE_MAP = {
    "running": "run",
    "trail running": "trail_run",
    "treadmill running": "treadmill",
    "cycling": "bike",
    "mountain biking": "bike",
    "swimming": "swim",
    "walking": "walk",
    "hiking": "hike",
    "kayaking": "kayak",
    "rowing": "row",
    "yoga": "yoga",
}

def _runkeeper_type(raw: str) -> str:
    return _RUNKEEPER_TYPE_MAP.get(raw.lower(), raw.lower() or "other")


def _parse_row(row: dict, csv_dir: Path, source: str):
    from ingestion.base import NormalizedActivity

    activity_type_raw = row.get("Type", "Running").strip().lower()
    activity_type = _runkeeper_type(activity_type_raw)

    date_str = row.get("Date", "").strip()
    if not date_str:
        return None
    try:
        start_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            start_time = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

    # Distance in km → meters
    dist_km_str = row.get("Distance (km)", "").strip()
    if not dist_km_str:
        return None
    try:
        distance_m = float(dist_km_str) * 1000
    except ValueError:
        return None

    if distance_m == 0:
        return None

    duration = _parse_duration(row.get("Duration", ""))

    # Elevation in meters
    climb_str = row.get("Climb (m)", "").strip()
    elevation_gain = float(climb_str) if climb_str else None

    avg_hr_str = row.get("Average Heart Rate (bpm)", "").strip()
    avg_hr = int(avg_hr_str) if avg_hr_str else None

    cal_str = row.get("Calories Burned", "").strip()
    calories = int(float(cal_str)) if cal_str else None

    notes = row.get("Notes", "").strip() or None

    # GPX file
    gpx_file_name = row.get("GPX File", "").strip()
    metadata = {
        "start_time": start_time,
        "duration_seconds": duration,
        "distance_meters": distance_m,
        "activity_type": activity_type,
        "elevation_gain_meters": elevation_gain,
        "avg_heart_rate": avg_hr,
        "calories": calories,
        "notes": notes,
        "title": row.get("Route Name", "").strip() or None,
    }

    if gpx_file_name:
        gpx_path = csv_dir / gpx_file_name
        if gpx_path.exists():
            return parse_gpx_file(gpx_path, source, metadata=metadata)

    # No GPX — create activity from metadata only
    return NormalizedActivity(
        source=source,
        start_time=start_time,
        duration_seconds=duration or 0,
        distance_meters=distance_m,
        activity_type=activity_type,
        elevation_gain_meters=elevation_gain,
        avg_heart_rate=avg_hr,
        calories=calories,
        notes=notes,
        title=metadata["title"],
    )
