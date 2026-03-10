"""Initialize the database schema. Safe to run multiple times (idempotent)."""
import sys
from pathlib import Path

# Allow running from the migrations/ directory or the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Base, engine
import models  # noqa: F401 — registers all models with Base


def init():
    Base.metadata.create_all(engine)
    print(f"Database initialized at: {engine.url}")
    # Print table names
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables: {', '.join(tables)}")


if __name__ == "__main__":
    init()
