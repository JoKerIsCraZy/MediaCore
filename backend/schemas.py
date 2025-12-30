from pydantic import BaseModel, Field
from typing import Optional, List as ListType, Any
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    MOVIE = "movie"
    TV = "tv"


class FilterOperator(str, Enum):
    AND = "and"
    OR = "or"


# ============ Filter Schemas ============

class FilterCondition(BaseModel):
    """A single filter condition."""
    field: str  # e.g., "vote_average", "genre", "year"
    operator: str  # e.g., "gte", "lte", "eq", "in", "not_in"
    value: Any  # The value to compare against


class FilterGroup(BaseModel):
    """A group of filter conditions."""
    operator: FilterOperator = FilterOperator.AND
    conditions: ListType[FilterCondition] = []


# ============ List Schemas ============

class ListBase(BaseModel):
    """Base schema for lists."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    media_type: MediaType = MediaType.MOVIE
    filters: ListType[dict] = []
    filter_operator: FilterOperator = FilterOperator.AND
    sort_by: str = "popularity.desc"
    limit: int = Field(default=100, ge=1, le=1000)
    auto_update: bool = True
    update_interval: int = Field(default=6, ge=1, le=168)


class ListCreate(ListBase):
    """Schema for creating a new list."""
    pass


class ListUpdate(BaseModel):
    """Schema for updating a list."""
    name: Optional[str] = None
    description: Optional[str] = None
    filters: Optional[ListType[dict]] = None
    filter_operator: Optional[FilterOperator] = None
    sort_by: Optional[str] = None
    limit: Optional[int] = None
    auto_update: Optional[bool] = None
    update_interval: Optional[int] = None


class ListItemResponse(BaseModel):
    """Schema for list item response."""
    id: int
    tmdb_id: int
    imdb_id: Optional[str] = None
    media_type: MediaType
    title: Optional[str] = None
    original_title: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None
    position: int
    added_at: datetime

    class Config:
        from_attributes = True


class ListResponse(ListBase):
    """Schema for list response."""
    id: int
    last_updated: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    item_count: int = 0

    class Config:
        from_attributes = True


class ListDetailResponse(ListResponse):
    """Schema for detailed list response with items."""
    items: ListType[ListItemResponse] = []


# ============ Media Schemas ============

class MediaBase(BaseModel):
    """Base schema for media items."""
    tmdb_id: int
    imdb_id: Optional[str] = None
    media_type: MediaType
    title: str
    original_title: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None


class MediaSearchResult(MediaBase):
    """Schema for search results."""
    genre_ids: ListType[int] = []


class MediaDetail(MediaBase):
    """Schema for detailed media info."""
    genres: ListType[dict] = []
    runtime: Optional[int] = None
    status: Optional[str] = None
    tagline: Optional[str] = None
    budget: Optional[int] = None
    revenue: Optional[int] = None
    keywords: ListType[str] = []
    cast: ListType[dict] = []
    crew: ListType[dict] = []
    watch_providers: Optional[dict] = None
    # Ratings from multiple sources
    ratings: dict = {}


class DiscoverRequest(BaseModel):
    """Schema for discover/filter request."""
    media_type: MediaType = MediaType.MOVIE
    filters: ListType[dict] = []
    filter_operator: FilterOperator = FilterOperator.AND
    sort_by: str = "popularity.desc"
    page: int = Field(default=1, ge=1)


class DiscoverResponse(BaseModel):
    """Schema for discover response."""
    results: ListType[MediaSearchResult]
    page: int
    total_pages: int
    total_results: int


# ============ Export Schemas ============

class RadarrExportItem(BaseModel):
    """Schema for Radarr import format."""
    title: str
    tmdbId: int
    imdbId: Optional[str] = None
    year: Optional[int] = None


class SonarrExportItem(BaseModel):
    """Schema for Sonarr import format."""
    title: str
    tvdbId: Optional[int] = None
    imdbId: Optional[str] = None
    year: Optional[int] = None


# ============ Saved Filter Schemas ============

class SavedFilterCreate(BaseModel):
    """Schema for creating a saved filter."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    filters: ListType[dict] = []
    filter_operator: FilterOperator = FilterOperator.AND


class SavedFilterResponse(SavedFilterCreate):
    """Schema for saved filter response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
