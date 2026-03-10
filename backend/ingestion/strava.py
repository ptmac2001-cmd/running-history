from __future__ import annotations
"""Strava importer — bulk export (CSV + GPX/FIT files)."""
import csv
import zipfile
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from sqlalchemy.orm import Session
from ingestion.base import BaseImporter, ImportResult
from ingestion.deduplication import insert_activity
from utils.gpx_parser import parse_gpx_file
from utils.fit_parser import parse_fit_file


_STRAVA_TYPE_MAP = {
    "run": "run",
    "trail run": "trail_run",
    "treadmill run": "treadmill",
    "virtual run": "run",
    "race": "race",
    "ride": "bike",
    "virtual ride": "bike",
    "mountain bike ride": "bike",
    "gravel ride": "bike",
    "e-bike ride": "bike",
    "swim": "swim",
    "open water swim": "swim",
    "walk": "walk",
    "hike": "hike",
    "kayaking": "kayak",
    "canoeing": "kayak",
    "rowing": "row",
    "yoga": "yoga",
    "workout": "workout",
    "weight training": "strength",
    "crossfit": "strength",
}

def _strava_type(raw: str) -> str:
    return _STRAVA_TYPE_MAP.get(raw.lower(), raw.lower() or "other")


class StravaImporter(BaseImporter):
    source_name = "strava"

    def run(self, data_dir: Path, db: Session) -> ImportResult:
        result = ImportResult(source=self.source_name)

        # Extract zip if present
        for item in data_dir.iterdir():
            if item.suffix.lower() == ".zip":
                with zipfile.ZipFile(item) as zf:
                    zf.extractall(data_dir / "extracted")

        # Find activities.csv
        csv_files = list(data_dir.rglob("activities.csv"))
        if not csv_files:
            print(f"[strava] No activities.csv found in {data_dir}")
            return result

        csv_path = csv_files[0]
        activities_dir = csv_path.parent

        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        result.total = len(rows)

        for row in tqdm(rows, desc="Strava activities"):
            try:
                activity = _parse_row(row, activities_dir, self.source_name)
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
                result.error_messages.append(f"{row.get('Activity ID', '?')}: {e}")

        return result


def _parse_row(row: dict, activities_dir: Path, source: str):
    activity_type_raw = row.get("Activity Type", "").strip().lower()
    activity_type = _strava_type(activity_type_raw)

    date_str = row.get("Activity Date", "").strip()
    if not date_str:
        return None
    # Strava format: "Jan 1, 2020, 8:00:00 AM" or ISO
    start_time = None
    for fmt in ("%b %d, %Y, %I:%M:%S %p", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            start_time = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            pass
    if start_time is None:
        return None

    # Distance in meters
    dist_str = row.get("Distance", "").strip()
    if not dist_str:
        return None
    try:
        distance_m = float(dist_str)  # Strava export is in meters
    except ValueError:
        return None

    if distance_m == 0:
        return None

    # Duration in seconds
    moving_time_str = row.get("Moving Time", "").strip()
    elapsed_time_str = row.get("Elapsed Time", "").strip()
    duration = _parse_seconds(elapsed_time_str) or _parse_seconds(moving_time_str) or 0
    moving_time = _parse_seconds(moving_time_str)

    elevation_gain_str = row.get("Elevation Gain", "").strip()
    elevation_gain = float(elevation_gain_str) if elevation_gain_str else None

    avg_hr_str = row.get("Average Heart Rate", "").strip()
    avg_hr = int(float(avg_hr_str)) if avg_hr_str else None

    max_hr_str = row.get("Max Heart Rate", "").strip()
    max_hr = int(float(max_hr_str)) if max_hr_str else None

    calories_str = row.get("Calories", "").strip()
    calories = int(float(calories_str)) if calories_str else None

    external_id = f"strava:{row.get('Activity ID', '').strip()}"
    title = row.get("Activity Name", "").strip() or None
    gear = row.get("Filename", "").strip() or None  # not gear, but placeholder

    metadata = {
        "start_time": start_time,
        "duration_seconds": duration,
        "distance_meters": distance_m,
        "activity_type": activity_type,
        "elevation_gain_meters": elevation_gain,
        "avg_heart_rate": avg_hr,
        "calories": calories,
        "title": title,
    }

    # Find the GPS file
    filename = row.get("Filename", "").strip()
    if filename:
        # Try relative to activities_dir
        gps_path = activities_dir / filename
        if not gps_path.exists():
            # Try just the basename
            gps_path = activities_dir / Path(filename).name
        if gps_path.exists():
            act = None
            if gps_path.suffix.lower() == ".fit":
                act = parse_fit_file(gps_path, source)
                if act:
                    # Override with CSV metadata where more reliable
                    act.start_time = start_time
                    act.duration_seconds = duration
                    act.moving_time_seconds = moving_time
                    act.distance_meters = distance_m
                    act.external_id = external_id
                    act.title = title
                    act.activity_type = activity_type
                    act.elevation_gain_meters = elevation_gain or act.elevation_gain_meters
                    act.avg_heart_rate = avg_hr or act.avg_heart_rate
                    act.max_heart_rate = max_hr or act.max_heart_rate
                    act.calories = calories or act.calories
            elif gps_path.suffix.lower() in (".gpx", ".gz"):
                # Handle .gpx.gz
                if str(gps_path).endswith(".gpx.gz"):
                    import gzip, shutil, tempfile
                    with gzip.open(gps_path, "rb") as gz_in:
                        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp:
                            shutil.copyfileobj(gz_in, tmp)
                            tmp_path = Path(tmp.name)
                    act = parse_gpx_file(tmp_path, source, metadata=metadata)
                    tmp_path.unlink(missing_ok=True)
                else:
                    act = parse_gpx_file(gps_path, source, metadata=metadata)
            if act:
                act.external_id = external_id
                return act

    # No GPS file — create from CSV metadata only
    from ingestion.base import NormalizedActivity
    return NormalizedActivity(
        source=source,
        external_id=external_id,
        start_time=start_time,
        duration_seconds=duration,
        moving_time_seconds=moving_time,
        distance_meters=distance_m,
        activity_type=activity_type,
        elevation_gain_meters=elevation_gain,
        avg_heart_rate=avg_hr,
        max_heart_rate=max_hr,
        calories=calories,
        title=title,
    )


def _parse_seconds(value: str) -> int | None:
    """Parse 'H:MM:SS' or plain seconds string."""
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    parts = value.split(":")
    try:
        parts = [int(p) for p in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
    except ValueError:
        pass
    return None
