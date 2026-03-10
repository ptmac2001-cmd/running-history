"""CLI: import from all sources in data/raw/."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from database import SessionLocal
from ingestion.garmin import GarminImporter
from ingestion.strava import StravaImporter
from ingestion.nike import NikeImporter
from ingestion.runkeeper import RunkeeperImporter
from ingestion.polar_suunto import PolarSuuntoImporter

BASE_RAW = Path(__file__).parent.parent.parent / "data" / "raw"

IMPORTERS = [
    ("garmin", GarminImporter()),
    ("strava", StravaImporter()),
    ("nike", NikeImporter()),
    ("runkeeper", RunkeeperImporter()),
    ("polar_suunto", PolarSuuntoImporter("polar")),
]


@click.command()
@click.option("--data-dir", default=str(BASE_RAW), help="Root raw data directory")
@click.option("--source", default=None, help="Only import this source (garmin, strava, nike, runkeeper, polar_suunto)")
def main(data_dir: str, source: str):
    raw = Path(data_dir)
    db = SessionLocal()
    try:
        for folder_name, importer in IMPORTERS:
            if source and folder_name != source:
                continue
            source_dir = raw / folder_name
            if not source_dir.exists():
                print(f"[{folder_name}] Directory not found: {source_dir} — skipping")
                continue
            result = importer.run(source_dir, db)
            print(result.summary())
            if result.error_messages:
                for msg in result.error_messages[:5]:
                    print(f"  ERROR: {msg}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
