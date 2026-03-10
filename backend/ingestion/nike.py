from __future__ import annotations
"""Nike Run Club importer — GDPR JSON export."""
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from tqdm import tqdm
from sqlalchemy.orm import Session
from ingestion.base import BaseImporter, ImportResult, NormalizedActivity, NormalizedRoutePoint
from ingestion.deduplication import insert_activity


class NikeImporter(BaseImporter):
    source_name = "nike"

    def run(self, data_dir: Path, db: Session) -> ImportResult:
        result = ImportResult(source=self.source_name)

        # Extract zips
        for item in data_dir.iterdir():
            if item.suffix.lower() == ".zip":
                with zipfile.ZipFile(item) as zf:
                    zf.extractall(data_dir / "extracted")

        # Handle TCX exports (nikeuserdata/tcx/ format)
        tcx_files = list(data_dir.rglob("*.tcx"))
        if tcx_files:
            from utils.gpx_parser import parse_tcx_file
            result.total += len(tcx_files)
            for tcx_path in tqdm(tcx_files, desc="Nike TCX files"):
                try:
                    activity = parse_tcx_file(tcx_path, source=self.source_name)
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
                    result.error_messages.append(f"{tcx_path.name}: {e}")

        # Find activity JSON files
        json_files = list(data_dir.rglob("*.json"))
        if not json_files and not tcx_files:
            print(f"[nike] No JSON or TCX files found in {data_dir}")
            return result

        activities = []
        for jf in json_files:
            try:
                with open(jf, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    activities.extend(data)
                elif isinstance(data, dict):
                    activities.append(data)
            except Exception:
                pass

        result.total = len(activities)

        for raw in tqdm(activities, desc="Nike activities"):
            try:
                activity = _parse_activity(raw, self.source_name)
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
                result.error_messages.append(f"{raw.get('id', '?')}: {e}")

        return result


def _parse_activity(raw: dict, source: str) -> NormalizedActivity | None:
    activity_type_raw = raw.get("type", "").upper()
    if activity_type_raw not in ("RUN", "GUIDED_RUN", "TRAIL_RUN", "TREADMILL"):
        return None

    activity_type = "run"
    if "TREADMILL" in activity_type_raw:
        activity_type = "treadmill"
    elif "TRAIL" in activity_type_raw:
        activity_type = "trail_run"

    start_epoch_ms = raw.get("startEpochMs")
    if not start_epoch_ms:
        return None
    start_time = datetime.fromtimestamp(start_epoch_ms / 1000, tz=timezone.utc).replace(tzinfo=None)

    # Parse summaries
    summaries = {s["metric"]: s["value"] for s in raw.get("summaries", []) if "metric" in s and "value" in s}

    distance_m = None
    for key in ("distance", "Distance"):
        if key in summaries:
            val = summaries[key]
            # Nike stores distance in km
            distance_m = float(val) * 1000
            break

    if not distance_m or distance_m == 0:
        return None

    active_duration_ms = summaries.get("active_duration", summaries.get("duration", 0))
    duration_s = int(float(active_duration_ms) / 1000) if active_duration_ms else 0

    avg_hr = summaries.get("avg_heart_rate") or summaries.get("heart_rate")
    calories = summaries.get("calories") or summaries.get("active_calories")

    # GPS points from moments or geoPoints
    route_points: list[NormalizedRoutePoint] = []
    geo_points = raw.get("geoPoints") or []
    if not geo_points:
        # Try moments
        for moment in raw.get("moments", []):
            if moment.get("type") == "gps":
                geo_points.append(moment)

    for i, gp in enumerate(geo_points):
        lat = gp.get("lat") or gp.get("latitude")
        lng = gp.get("lon") or gp.get("longitude") or gp.get("lng")
        if lat is None or lng is None:
            continue
        ts = None
        epoch_ms = gp.get("timestamp") or gp.get("epochMs")
        if epoch_ms:
            ts = datetime.fromtimestamp(float(epoch_ms) / 1000, tz=timezone.utc).replace(tzinfo=None)
        route_points.append(NormalizedRoutePoint(
            sequence=i,
            lat=float(lat),
            lng=float(lng),
            elevation_m=gp.get("elevation") or gp.get("altitude"),
            timestamp=ts,
        ))

    external_id = f"nike:{raw.get('id', '')}"

    return NormalizedActivity(
        source=source,
        external_id=external_id,
        start_time=start_time,
        duration_seconds=duration_s,
        distance_meters=distance_m,
        activity_type=activity_type,
        avg_heart_rate=int(avg_hr) if avg_hr else None,
        calories=int(float(calories)) if calories else None,
        route_points=route_points,
    )
