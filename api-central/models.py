"""
API Central - IMDb Data Models

This module contains SQLAlchemy models for IMDb data storage.
TMDB data is fetched live by the backend, not stored here.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ==========================================
# IMDb Dataset Models
# ==========================================

class ImdbRating(Base):
    """
    IMDb Ratings from title.ratings.tsv.gz
    Primary source for IMDb rating filters.
    """
    __tablename__ = "imdb_ratings"

    tconst = Column(String(20), primary_key=True)  # e.g., "tt1234567"
    averageRating = Column(Float, nullable=True, index=True)
    numVotes = Column(Integer, nullable=True, index=True)

    def __repr__(self):
        return f"<ImdbRating {self.tconst}: {self.averageRating} ({self.numVotes} votes)>"


class ImdbTitle(Base):
    """
    IMDb Title basics from title.basics.tsv.gz
    Contains title information for IMDb entries.
    """
    __tablename__ = "imdb_titles"

    tconst = Column(String(20), primary_key=True)
    titleType = Column(String(50), nullable=True, index=True)  # movie, tvSeries, etc.
    primaryTitle = Column(String(500), nullable=True, index=True)
    originalTitle = Column(String(500), nullable=True)
    isAdult = Column(Boolean, default=False)
    startYear = Column(Integer, nullable=True, index=True)
    endYear = Column(Integer, nullable=True)
    runtimeMinutes = Column(Integer, nullable=True)
    genres = Column(Text, nullable=True)  # Comma-separated genres

    def __repr__(self):
        return f"<ImdbTitle {self.tconst}: {self.primaryTitle}>"


class Movie(Base):
    """
    Movie cache table for TMDB <-> IMDb ID mapping.
    Populated on-the-fly when backend fetches from TMDB.
    Used by local_discover to find movies by IMDb ID.
    """
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)  # TMDB ID
    imdb_id = Column(String(20), index=True, nullable=True)
    title = Column(String(500), nullable=False)
    original_title = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)
    release_date = Column(String(20), nullable=True)
    vote_average = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    popularity = Column(Float, nullable=True)
    poster_path = Column(String(200), nullable=True)
    backdrop_path = Column(String(200), nullable=True)

    def __repr__(self):
        return f"<Movie {self.id}: {self.title}>"


class TVShow(Base):
    """
    TV Show cache table for TMDB <-> IMDb ID mapping.
    Populated on-the-fly when backend fetches from TMDB.
    """
    __tablename__ = "tv_shows"

    id = Column(Integer, primary_key=True)  # TMDB ID
    imdb_id = Column(String(20), index=True, nullable=True)
    tvdb_id = Column(Integer, index=True, nullable=True)
    name = Column(String(500), nullable=False)
    original_name = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)
    first_air_date = Column(String(20), nullable=True)
    vote_average = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    popularity = Column(Float, nullable=True)
    poster_path = Column(String(200), nullable=True)
    backdrop_path = Column(String(200), nullable=True)

    def __repr__(self):
        return f"<TVShow {self.id}: {self.name}>"
