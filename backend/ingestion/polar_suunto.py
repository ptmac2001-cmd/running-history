"""Polar/Suunto importer — FIT, GPX, and TCX files."""
from pathlib import Path
from tqdm import tqdm
from sqlalchemy.orm import Session
from ingestion.base import BaseImporter, ImportResult
from ingestion.deduplication import insert_activity
from utils.fit_parser import parse_fit_file
from utils.gpx_parser import parse_gpx_file, parse_tcx_file


class PolarSuuntoImporter(BaseImporter):
    source_name = "polar"  # overridden per file if needed

    def __init__(self, source_name: str = "polar"):
        self.source_name = source_name

    def run(self, data_dir: Path, db: Session) -> ImportResult:
        result = ImportResult(source=self.source_name)

        # Collect all supported files
        files: list[Path] = []
        for ext in ("*.fit", "*.FIT", "*.gpx", "*.GPX", "*.tcx", "*.TCX"):
            files.extend(data_dir.rglob(ext))

        result.total = len(files)
        if not files:
            print(f"[{self.source_name}] No FIT/GPX/TCX files found in {data_dir}")
            return result

        for path in tqdm(files, desc=f"{self.source_name} files"):
            try:
                activity = None
                suffix = path.suffix.lower()
                if suffix == ".fit":
                    activity = parse_fit_file(path, source=self.source_name)
                elif suffix == ".gpx":
                    activity = parse_gpx_file(path, source=self.source_name)
                elif suffix == ".tcx":
                    activity = parse_tcx_file(path, source=self.source_name)

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
                result.error_messages.append(f"{path.name}: {e}")

        return result
