"""
API Central Configuration

Configuration for the IMDb data import service.
"""

import os
from pathlib import Path

# Get the directories
API_CENTRAL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = API_CENTRAL_DIR.parent

# Database Configuration
DB_PATH = API_CENTRAL_DIR / "media_database.db"
DATABASE_URL = os.getenv("API_CENTRAL_DATABASE_URL", f"sqlite+aiosqlite:///{DB_PATH}")

# Ensure async driver is used
if DATABASE_URL.startswith("sqlite://") and "aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# IMDb data directory
IMDB_DATA_DIR = API_CENTRAL_DIR / "imdb_data"

# Batch size for database commits
BATCH_SIZE = 10000
