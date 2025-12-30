from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    """Type of media item."""
    MOVIE = "movie"
    TV = "tv"


class FilterOperator(str, Enum):
    """Logical operator for filter groups."""
    AND = "and"
    OR = "or"


class List(Base):
    """A user-created media list."""
    __tablename__ = "lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    media_type = Column(SQLEnum(MediaType), default=MediaType.MOVIE)
    
    # Filter configuration as JSON
    filters = Column(JSON, default=list)
    filter_operator = Column(SQLEnum(FilterOperator), default=FilterOperator.AND)
    
    # Sorting
    sort_by = Column(String(50), default="popularity.desc")
    limit = Column(Integer, default=100)
    
    # Auto-update settings
    auto_update = Column(Boolean, default=True)
    update_interval = Column(Integer, default=6)  # hours
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("ListItem", back_populates="list", cascade="all, delete-orphan")


class ListItem(Base):
    """An item (movie/show) in a list."""
    __tablename__ = "list_items"
    
    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("lists.id"), nullable=False)
    
    # Media identifiers
    tmdb_id = Column(Integer, nullable=False)
    imdb_id = Column(String(20))
    tvdb_id = Column(Integer)  # For TV shows (Sonarr)
    media_type = Column(SQLEnum(MediaType), default=MediaType.MOVIE)
    
    # Cached data for quick access
    title = Column(String(500))
    original_title = Column(String(500))
    poster_path = Column(String(255))
    backdrop_path = Column(String(255))
    overview = Column(Text)
    release_date = Column(String(20))
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float)
    
    # Position in list
    position = Column(Integer, default=0)
    
    # Timestamps
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    list = relationship("List", back_populates="items")


class MediaCache(Base):
    """Cache for TMDB data to reduce API calls."""
    __tablename__ = "media_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, nullable=False, index=True)
    media_type = Column(SQLEnum(MediaType), nullable=False)
    
    # Full TMDB response as JSON
    data = Column(JSON)
    
    # Cache metadata
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class SavedFilter(Base):
    """Saved filter presets for reuse."""
    __tablename__ = "saved_filters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    
    # Filter configuration
    filters = Column(JSON, default=list)
    filter_operator = Column(SQLEnum(FilterOperator), default=FilterOperator.AND)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
