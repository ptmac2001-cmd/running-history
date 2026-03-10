"""Rename metric columns to imperial in-place (no data loss)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import engine
from sqlalchemy import text

renames = [
    # (table, old_name, new_name)
    ("activities", "distance_meters",       "distance_miles"),
    ("activities", "elevation_gain_meters", "elevation_gain_feet"),
    ("activities", "elevation_loss_meters", "elevation_loss_feet"),
    ("activities", "avg_pace_sec_per_km",   "avg_pace_sec_per_mile"),
    ("activities", "avg_speed_mps",         "avg_speed_mph"),
    ("activities", "max_speed_mps",         "max_speed_mph"),
    ("route_points", "elevation_m",         "elevation_ft"),
    ("route_points", "speed_mps",           "speed_mph"),
    ("route_points", "distance_m",          "distance_mi"),
    ("laps", "distance_meters",             "distance_miles"),
    ("laps", "avg_pace_sec_per_km",         "avg_pace_sec_per_mile"),
    ("laps", "elevation_gain_m",            "elevation_gain_ft"),
]

# Conversion factors
M_TO_MI  = 0.000621371
M_TO_FT  = 3.28084
MPS_TO_MPH = 2.23694
SEC_PER_KM_TO_SEC_PER_MI = 1.60934

# Which columns need value conversion and by what factor
conversions = {
    ("activities",  "distance_miles"):        M_TO_MI,
    ("activities",  "elevation_gain_feet"):   M_TO_FT,
    ("activities",  "elevation_loss_feet"):   M_TO_FT,
    ("activities",  "avg_pace_sec_per_mile"): SEC_PER_KM_TO_SEC_PER_MI,
    ("activities",  "avg_speed_mph"):         MPS_TO_MPH,
    ("activities",  "max_speed_mph"):         MPS_TO_MPH,
    ("route_points","elevation_ft"):          M_TO_FT,
    ("route_points","speed_mph"):             MPS_TO_MPH,
    ("route_points","distance_mi"):           M_TO_MI,
    ("laps",        "distance_miles"):        M_TO_MI,
    ("laps",        "avg_pace_sec_per_mile"): SEC_PER_KM_TO_SEC_PER_MI,
    ("laps",        "elevation_gain_ft"):     M_TO_FT,
}

with engine.begin() as conn:
    # 1. Rename columns
    for table, old, new in renames:
        try:
            conn.execute(text(f'ALTER TABLE "{table}" RENAME COLUMN "{old}" TO "{new}"'))
            print(f"  renamed {table}.{old} -> {new}")
        except Exception as e:
            print(f"  skipped {table}.{old}: {e}")

    # 2. Convert values
    for (table, col), factor in conversions.items():
        conn.execute(text(f'UPDATE "{table}" SET "{col}" = "{col}" * {factor} WHERE "{col}" IS NOT NULL'))
        print(f"  converted {table}.{col} (* {factor})")

print("Done.")
