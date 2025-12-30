from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)  # TMDB ID
    imdb_id = Column(String(20), index=True, nullable=True)

    # Basic info
    title = Column(String(500), nullable=False)
    original_title = Column(String(500), nullable=True)
    original_language = Column(String(10), nullable=True)
    overview = Column(Text, nullable=True)
    tagline = Column(String(500), nullable=True)

    # Release info
    release_date = Column(String(20), nullable=True)
    status = Column(String(50), nullable=True)  # Released, Post Production, etc.

    # Ratings
    vote_average = Column(Float, nullable=True)  # TMDB rating
    vote_count = Column(Integer, nullable=True)
    popularity = Column(Float, nullable=True)

    # Technical info
    runtime = Column(Integer, nullable=True)  # in minutes
    budget = Column(Integer, nullable=True)
    revenue = Column(Integer, nullable=True)

    # Media
    poster_path = Column(String(200), nullable=True)
    backdrop_path = Column(String(200), nullable=True)

    # Genres and production
    genres = Column(JSON, nullable=True)  # List of genre objects
    production_countries = Column(JSON, nullable=True)
    production_companies = Column(JSON, nullable=True)
    spoken_languages = Column(JSON, nullable=True)

    # Keywords
    keywords = Column(JSON, nullable=True)  # List of keyword objects

    # Credits
    cast = Column(JSON, nullable=True)  # Top actors
    crew = Column(JSON, nullable=True)  # Directors, writers, etc.
    directors = Column(JSON, nullable=True)  # Extracted directors

    # Streaming / Watch Providers (per region)
    watch_providers = Column(JSON, nullable=True)  # {region: {flatrate: [], rent: [], buy: []}}

    # Release dates per region
    release_dates = Column(JSON, nullable=True)  # {region: [{type, date, certification}]}
    certifications = Column(JSON, nullable=True)  # Age ratings per region

    # Alternative titles
    alternative_titles = Column(JSON, nullable=True)

    # Videos (trailers, etc.)
    videos = Column(JSON, nullable=True)

    # Recommendations and similar
    recommendations = Column(JSON, nullable=True)  # List of similar movie IDs
    similar = Column(JSON, nullable=True)

    # Collection info
    belongs_to_collection = Column(JSON, nullable=True)

    # Additional
    adult = Column(Boolean, default=False)
    video = Column(Boolean, default=False)
    homepage = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Movie {self.id}: {self.title}>"


class TVShow(Base):
    __tablename__ = "tv_shows"

    id = Column(Integer, primary_key=True)  # TMDB ID
    imdb_id = Column(String(20), index=True, nullable=True)
    tvdb_id = Column(Integer, index=True, nullable=True)

    # Basic info
    name = Column(String(500), nullable=False)
    original_name = Column(String(500), nullable=True)
    original_language = Column(String(10), nullable=True)
    overview = Column(Text, nullable=True)
    tagline = Column(String(500), nullable=True)

    # Airing info
    first_air_date = Column(String(20), nullable=True)
    last_air_date = Column(String(20), nullable=True)
    next_episode_to_air = Column(JSON, nullable=True)
    last_episode_to_air = Column(JSON, nullable=True)
    status = Column(String(50), nullable=True)  # Returning Series, Ended, etc.
    type = Column(String(50), nullable=True)  # Scripted, Reality, etc.

    # Ratings
    vote_average = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    popularity = Column(Float, nullable=True)

    # Episode info
    number_of_seasons = Column(Integer, nullable=True)
    number_of_episodes = Column(Integer, nullable=True)
    episode_run_time = Column(JSON, nullable=True)  # List of runtimes
    seasons = Column(JSON, nullable=True)  # Season details

    # Media
    poster_path = Column(String(200), nullable=True)
    backdrop_path = Column(String(200), nullable=True)

    # Genres and production
    genres = Column(JSON, nullable=True)
    production_countries = Column(JSON, nullable=True)
    production_companies = Column(JSON, nullable=True)
    spoken_languages = Column(JSON, nullable=True)
    networks = Column(JSON, nullable=True)  # TV networks
    origin_country = Column(JSON, nullable=True)

    # Keywords
    keywords = Column(JSON, nullable=True)

    # Credits
    cast = Column(JSON, nullable=True)
    crew = Column(JSON, nullable=True)
    created_by = Column(JSON, nullable=True)  # Show creators

    # Streaming / Watch Providers (per region)
    watch_providers = Column(JSON, nullable=True)  # {region: {flatrate: [], rent: [], buy: []}}

    # Content ratings per region
    content_ratings = Column(JSON, nullable=True)  # Age ratings per region

    # Alternative titles
    alternative_titles = Column(JSON, nullable=True)

    # Videos (trailers, etc.)
    videos = Column(JSON, nullable=True)

    # Recommendations and similar
    recommendations = Column(JSON, nullable=True)
    similar = Column(JSON, nullable=True)

    # Additional
    adult = Column(Boolean, default=False)
    in_production = Column(Boolean, default=False)
    homepage = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TVShow {self.id}: {self.name}>"


class WatchProvider(Base):
    """Reference table for all known watch providers."""
    __tablename__ = "watch_providers"

    id = Column(Integer, primary_key=True)  # Provider ID from TMDB
    name = Column(String(200), nullable=False)
    logo_path = Column(String(200), nullable=True)
    display_priority = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<WatchProvider {self.id}: {self.name}>"


class Genre(Base):
    """Reference table for all genres."""
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    media_type = Column(String(20), nullable=False)  # 'movie' or 'tv'

    def __repr__(self):
        return f"<Genre {self.id}: {self.name}>"


class SyncProgress(Base):
    """Track sync progress for resumable operations."""
    __tablename__ = "sync_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    media_type = Column(String(20), nullable=False)  # 'movie' or 'tv'
    last_page = Column(Integer, default=0)
    total_pages = Column(Integer, nullable=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="in_progress")  # in_progress, completed

    def __repr__(self):
        return f"<SyncProgress {self.media_type}: page {self.last_page}/{self.total_pages}>"


# ==========================================
# IMDb Dataset Models (for full import)
# ==========================================

class ImdbTitle(Base):
    """From title.basics.tsv.gz"""
    __tablename__ = "imdb_titles"

    tconst = Column(String(20), primary_key=True)
    titleType = Column(String(50), nullable=True, index=True)
    primaryTitle = Column(String(500), nullable=True, index=True)
    originalTitle = Column(String(500), nullable=True)
    isAdult = Column(Boolean, default=False)
    startYear = Column(Integer, nullable=True, index=True)
    endYear = Column(Integer, nullable=True)
    runtimeMinutes = Column(Integer, nullable=True)
    genres = Column(Text, nullable=True)  # Comma separated string because it's from TSV

    def __repr__(self):
        return f"<ImdbTitle {self.tconst}: {self.primaryTitle}>"


class ImdbRating(Base):
    """From title.ratings.tsv.gz"""
    __tablename__ = "imdb_ratings"

    tconst = Column(String(20), primary_key=True)
    averageRating = Column(Float, nullable=True, index=True)
    numVotes = Column(Integer, nullable=True, index=True)

    def __repr__(self):
        return f"<ImdbRating {self.tconst}: {self.averageRating}>"


class ImdbAka(Base):
    """From title.akas.tsv.gz"""
    __tablename__ = "imdb_akas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titleId = Column(String(20), index=True, nullable=False)  # FK to tconst, but we might not enforce FK for speed
    ordering = Column(Integer, nullable=True)
    title = Column(String(500), nullable=True, index=True)
    region = Column(String(10), nullable=True, index=True)
    language = Column(String(10), nullable=True)
    types = Column(String(50), nullable=True)
    attributes = Column(String(200), nullable=True)
    isOriginalTitle = Column(Boolean, default=False)

    def __repr__(self):
        return f"<ImdbAka {self.titleId}: {self.title} ({self.region})>"


class ImdbPrincipal(Base):
    """From title.principals.tsv.gz (Cast & Crew)"""
    __tablename__ = "imdb_principals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tconst = Column(String(20), index=True, nullable=False)
    ordering = Column(Integer, nullable=True)
    nconst = Column(String(20), index=True, nullable=True)
    category = Column(String(50), nullable=True, index=True)  # actor, director, etc.
    job = Column(String(200), nullable=True)
    characters = Column(Text, nullable=True)  # JSON string in TSV usually

    def __repr__(self):
        return f"<ImdbPrincipal {self.tconst} -> {self.nconst} ({self.category})>"

