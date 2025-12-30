from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from datetime import datetime
from database import Base

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
    status = Column(String(50), nullable=True)

    # Ratings
    vote_average = Column(Float, nullable=True)  # TMDB rating
    vote_count = Column(Integer, nullable=True)
    popularity = Column(Float, nullable=True)

    # Technical info
    runtime = Column(Integer, nullable=True)
    budget = Column(Integer, nullable=True)
    revenue = Column(Integer, nullable=True)

    # Media
    poster_path = Column(String(200), nullable=True)
    backdrop_path = Column(String(200), nullable=True)

    # Genres and production
    genres = Column(JSON, nullable=True)
    production_countries = Column(JSON, nullable=True)
    production_companies = Column(JSON, nullable=True)
    spoken_languages = Column(JSON, nullable=True)

    # Keywords
    keywords = Column(JSON, nullable=True)

    # Credits
    cast = Column(JSON, nullable=True)
    crew = Column(JSON, nullable=True)
    directors = Column(JSON, nullable=True)

    # Streaming / Watch Providers (per region)
    watch_providers = Column(JSON, nullable=True)

    # Release dates per region
    release_dates = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)

    # Alternative titles
    alternative_titles = Column(JSON, nullable=True)

    # Videos
    videos = Column(JSON, nullable=True)

    # Recommendations and similar
    recommendations = Column(JSON, nullable=True)
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


class ImdbRating(Base):
    """From title.ratings.tsv.gz"""
    __tablename__ = "imdb_ratings"

    tconst = Column(String(20), primary_key=True)
    averageRating = Column(Float, nullable=True, index=True)
    numVotes = Column(Integer, nullable=True, index=True)

class Genre(Base):
    """Reference table for all genres."""
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    media_type = Column(String(20), nullable=False)  # 'movie' or 'tv'
