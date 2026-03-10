"""Garmin Connect importer — bulk FIT export mode."""
import zipfile
from pathlib import Path
from tqdm import tqdm
from sqlalchemy.orm import Session
from ingestion.base import BaseImporter, ImportResult
from ingestion.deduplication import insert_activity
from utils.fit_parser import parse_fit_file


class GarminImporter(BaseImporter):
    source_name = "garmin"

    def run(self, data_dir: Path, db: Session) -> ImportResult:
        result = ImportResult(source=self.source_name)

        # Collect .fit files — may be directly in data_dir or inside a zip
        fit_files: list[Path] = []

        for item in data_dir.iterdir():
            if item.suffix.lower() == ".zip":
                fit_files.extend(_extract_fits_from_zip(item, data_dir))
            elif item.suffix.lower() == ".fit":
                fit_files.append(item)

        # Also search subdirectories (Garmin export puts fits in activity/ folder)
        fit_files.extend(p for p in data_dir.rglob("*.fit") if p not in fit_files)
        fit_files = list(set(fit_files))

        result.total = len(fit_files)
        if not fit_files:
            print(f"[garmin] No .fit files found in {data_dir}")
            return result

        for fit_path in tqdm(fit_files, desc="Garmin FIT files"):
            try:
                activity = parse_fit_file(fit_path, source=self.source_name)
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
                result.error_messages.append(f"{fit_path.name}: {e}")

        return result


def _extract_fits_from_zip(zip_path: Path, target_dir: Path) -> list[Path]:
    """Extract .fit files from a zip archive into target_dir/garmin_extracted/."""
    extract_dir = target_dir / "garmin_extracted"
    extract_dir.mkdir(exist_ok=True)
    extracted = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.lower().endswith(".fit"):
                zf.extract(name, extract_dir)
                extracted.append(extract_dir / name)
    return extracted
