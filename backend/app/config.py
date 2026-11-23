"""Application paths and constants (all relative to the project, never absolute)."""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = Path(os.environ.get("COURIER_DATA_DIR", BACKEND_DIR / "data"))
FRONTEND_DIST = Path(os.environ.get("COURIER_FRONTEND_DIST", PROJECT_DIR / "frontend" / "dist"))
SAMPLE_DIR = PROJECT_DIR / "sample_data"

APP_NAME = "Mini-Courier Planner"
APP_VERSION = "1.0.1"

DEFAULT_SETTINGS = {
    "capacity": 120,
    "depot": "Depot",
    "dispatch_time": "2026-12-01T09:00",
    "speed_kmph": 30.0,
    "service_minutes": 5,
}
