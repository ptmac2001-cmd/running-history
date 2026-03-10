"""Heart rate zone calculations (5-zone model)."""

ZONE_LABELS = {
    1: "Zone 1 (Recovery)",
    2: "Zone 2 (Aerobic)",
    3: "Zone 3 (Tempo)",
    4: "Zone 4 (Threshold)",
    5: "Zone 5 (Anaerobic)",
}

# Zone boundaries as fraction of max HR
ZONE_BOUNDARIES = [
    (0.00, 0.60),  # Zone 1
    (0.60, 0.70),  # Zone 2
    (0.70, 0.80),  # Zone 3
    (0.80, 0.90),  # Zone 4
    (0.90, 1.01),  # Zone 5
]


def get_zone(heart_rate: int, max_hr: int) -> int:
    """Return zone number (1-5) for a given heart rate."""
    fraction = heart_rate / max_hr
    for zone, (lo, hi) in enumerate(ZONE_BOUNDARIES, start=1):
        if lo <= fraction < hi:
            return zone
    return 5


def calculate_zones(hr_seconds: list[tuple[int, int]], max_hr: int) -> list[dict]:
    """
    Calculate time spent in each zone.
    hr_seconds: list of (heart_rate, seconds_at_this_hr) pairs
    Returns list of zone dicts with zone, label, seconds, percentage.
    """
    zone_seconds = {z: 0 for z in range(1, 6)}
    total = 0

    for hr, secs in hr_seconds:
        if hr and hr > 0:
            z = get_zone(hr, max_hr)
            zone_seconds[z] += secs
            total += secs

    return [
        {
            "zone": z,
            "label": ZONE_LABELS[z],
            "seconds": zone_seconds[z],
            "percentage": round(zone_seconds[z] / total * 100, 1) if total > 0 else 0.0,
        }
        for z in range(1, 6)
    ]
