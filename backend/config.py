from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/jokerlist.db"
    media_database_url: str = "sqlite+aiosqlite:///../api-central/media_database.db"
    
    # TMDB API
    tmdb_api_key: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_image_base_url: str = "https://image.tmdb.org/t/p"
    
    # Scheduler
    update_interval: int = 6  # hours
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Optional: Trakt integration
    trakt_client_id: str = ""
    trakt_client_secret: str = ""
    
    # App settings
    app_name: str = "MediaCore"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
