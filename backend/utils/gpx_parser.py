from __future__ import annotations
"""Parse GPX and TCX files into NormalizedActivity."""
from datetime import datetime
from pathlib import Path
from ingestion.base import NormalizedActivity, NormalizedRoutePoint


def parse_gpx_file(path: Path, source: str, metadata: dict | None = None) -> NormalizedActivity | None:
    """Parse a .gpx file. metadata can override summary fields (from CSV row etc.)."""
    try:
        import gpxpy
    except ImportError:
        raise ImportError("gpxpy is required: pip install gpxpy")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        try:
            gpx = gpxpy.parse(f)
        except Exception:
            return None

    route_points: list[NormalizedRoutePoint] = []
    sequence = 0

    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                if pt.latitude is None or pt.longitude is None:
                    continue
                ts = pt.time
                if ts and ts.tzinfo:
                    ts = ts.replace(tzinfo=None)
                route_points.append(NormalizedRoutePoint(
                    sequence=sequence,
                    lat=pt.latitude,
                    lng=pt.longitude,
                    elevation_m=pt.elevation,
                    timestamp=ts,
                ))
                sequence += 1

    if not route_points and not metadata:
        return None

    # Derive summary from metadata or from tracks
    if metadata:
        start_time = metadata.get("start_time")
        duration = metadata.get("duration_seconds")
        distance = metadata.get("distance_meters")
        title = metadata.get("title")
        activity_type = metadata.get("activity_type", "run")
        elevation_gain = metadata.get("elevation_gain_meters")
        avg_hr = metadata.get("avg_heart_rate")
        calories = metadata.get("calories")
        notes = metadata.get("notes")
        gear = metadata.get("gear_name")
    else:
        # Derive from GPX data itself
        if not route_points:
            return None
        start_time = route_points[0].timestamp
        if not start_time:
            return None
        end_time = route_points[-1].timestamp
        duration = int((end_time - start_time).total_seconds()) if end_time else None
        # Estimate distance from haversine
        distance = _estimate_distance(route_points)
        title = None
        activity_type = "run"
        elevation_gain = None
        avg_hr = None
        calories = None
        notes = None
        gear = None

    if not start_time or not distance or distance == 0:
        return None
    if not duration:
        duration = 0

    return NormalizedActivity(
        source=source,
        start_time=start_time,
        duration_seconds=int(duration),
        distance_meters=float(distance),
        title=title,
        activity_type=activity_type,
        elevation_gain_meters=elevation_gain,
        avg_heart_rate=avg_hr,
        calories=calories,
        notes=notes,
        gear_name=gear,
        raw_file_path=str(path),
        route_points=route_points,
    )


def parse_tcx_file(path: Path, source: str) -> NormalizedActivity | None:
    """Parse a Polar/Suunto .tcx file."""
    try:
        from lxml import etree
    except ImportError:
        raise ImportError("lxml is required: pip install lxml")

    try:
        tree = etree.parse(str(path))
    except Exception:
        return None

    root = tree.getroot()
    ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}

    activities_el = root.findall(".//tcx:Activity", ns)
    if not activities_el:
        # try without namespace
        ns = {}
        activities_el = root.findall(".//Activity")

    if not activities_el:
        return None

    act_el = activities_el[0]
    sport = act_el.get("Sport", "Running").lower()
    _TCX_SPORT_MAP = {
        "running": "run",
        "biking": "bike",
        "cycling": "bike",
        "swimming": "swim",
        "walking": "walk",
        "hiking": "hike",
        "other": "other",
    }
    activity_type = _TCX_SPORT_MAP.get(sport, sport or "other")

    route_points: list[NormalizedRoutePoint] = []
    sequence = 0
    total_distance = 0.0
    total_time = 0
    total_calories = 0
    start_time = None
    hr_values = []

    prefix = "tcx:" if ns else ""

    for lap_el in act_el.findall(f"{prefix}Lap" if ns else "Lap", ns):
        lap_start = lap_el.get("StartTime")
        if lap_start and start_time is None:
            try:
                start_time = datetime.fromisoformat(lap_start.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                pass

        dist_el = lap_el.find(f"{prefix}DistanceMeters" if ns else "DistanceMeters", ns)
        if dist_el is not None and dist_el.text:
            total_distance += float(dist_el.text)

        time_el = lap_el.find(f"{prefix}TotalTimeSeconds" if ns else "TotalTimeSeconds", ns)
        if time_el is not None and time_el.text:
            total_time += int(float(time_el.text))

        cal_el = lap_el.find(f"{prefix}Calories" if ns else "Calories", ns)
        if cal_el is not None and cal_el.text:
            total_calories += int(cal_el.text)

        for tp_el in lap_el.findall(f".//{prefix}Trackpoint" if ns else ".//Trackpoint", ns):
            ts_el = tp_el.find(f"{prefix}Time" if ns else "Time", ns)
            ts = None
            if ts_el is not None and ts_el.text:
                try:
                    ts = datetime.fromisoformat(ts_el.text.replace("Z", "+00:00")).replace(tzinfo=None)
                except ValueError:
                    pass

            pos_el = tp_el.find(f"{prefix}Position" if ns else "Position", ns)
            lat = lng = None
            if pos_el is not None:
                lat_el = pos_el.find(f"{prefix}LatitudeDegrees" if ns else "LatitudeDegrees", ns)
                lng_el = pos_el.find(f"{prefix}LongitudeDegrees" if ns else "LongitudeDegrees", ns)
                if lat_el is not None and lat_el.text:
                    lat = float(lat_el.text)
                if lng_el is not None and lng_el.text:
                    lng = float(lng_el.text)

            if lat is None or lng is None:
                continue

            alt_el = tp_el.find(f"{prefix}AltitudeMeters" if ns else "AltitudeMeters", ns)
            elevation = float(alt_el.text) if alt_el is not None and alt_el.text else None

            hr_el = tp_el.find(f".//{prefix}Value" if ns else ".//Value", ns)
            hr = None
            if hr_el is not None and hr_el.text:
                try:
                    hr = int(hr_el.text)
                    hr_values.append(hr)
                except ValueError:
                    pass

            dist_pt_el = tp_el.find(f"{prefix}DistanceMeters" if ns else "DistanceMeters", ns)
            dist_pt = float(dist_pt_el.text) if dist_pt_el is not None and dist_pt_el.text else None

            route_points.append(NormalizedRoutePoint(
                sequence=sequence,
                lat=lat,
                lng=lng,
                elevation_m=elevation,
                timestamp=ts,
                heart_rate=hr,
                distance_m=dist_pt,
            ))
            sequence += 1

    if not start_time or total_distance == 0:
        return None

    avg_hr = int(sum(hr_values) / len(hr_values)) if hr_values else None

    return NormalizedActivity(
        source=source,
        start_time=start_time,
        duration_seconds=total_time,
        distance_meters=total_distance,
        activity_type=activity_type,
        avg_heart_rate=avg_hr,
        calories=total_calories if total_calories > 0 else None,
        raw_file_path=str(path),
        route_points=route_points,
    )


def _estimate_distance(points: list[NormalizedRoutePoint]) -> float:
    """Rough haversine distance in meters."""
    import math
    total = 0.0
    for i in range(1, len(points)):
        a, b = points[i - 1], points[i]
        lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
        dlat = lat2 - lat1
        dlng = math.radians(b.lng - a.lng)
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        total += 2 * 6371000 * math.asin(math.sqrt(h))
    return total
