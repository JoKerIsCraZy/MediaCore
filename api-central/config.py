import os
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory (parent of api-central/)
API_CENTRAL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = API_CENTRAL_DIR.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")

# TMDB API Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Database Configuration
DB_PATH = API_CENTRAL_DIR / "media_database.db"
DATABASE_URL = os.getenv("API_CENTRAL_DATABASE_URL", f"sqlite+aiosqlite:///{DB_PATH}")

if DATABASE_URL.startswith("sqlite://") and "aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# Rate limiting (TMDB allows ~40 requests per 10 seconds)
RATE_LIMIT_REQUESTS = 35
RATE_LIMIT_PERIOD = 10  # seconds

# Batch size for database commits
BATCH_SIZE = 100
