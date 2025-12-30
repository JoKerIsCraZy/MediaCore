import os
from dotenv import load_dotenv

load_dotenv()

# TMDB API Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Database Configuration
# Use absolute path for Windows compatibility
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "media_database.db"
# Ensure we always use the async driver
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DB_PATH}")

if DATABASE_URL.startswith("sqlite://") and "aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# Rate limiting (TMDB allows ~40 requests per 10 seconds)
RATE_LIMIT_REQUESTS = 35
RATE_LIMIT_PERIOD = 10  # seconds

# Batch size for database commits
BATCH_SIZE = 100
