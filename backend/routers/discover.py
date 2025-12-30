from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict
import json
from services.local_discover import local_discover_service

router = APIRouter(prefix="/discover", tags=["Discover"])

@router.get("")
async def discover_movies(
    page: int = Query(1, ge=1),
    sort_by: str = Query("popularity.desc"),
    filters: Optional[str] = Query(None, description="JSON string of filters") 
):
    """
    Discover movies using local database with IMDb integration.
    Filters passed as JSON string: [{"field": "imdb_rating", "operator": "gte", "value": 8}]
    """
    parsed_filters = []
    if filters:
        try:
            parsed_filters = json.loads(filters)
        except json.JSONDecodeError:
            pass
            
    # For backward compatibility or ease of use, we can also accept query params directly
    # But for the filter builder, the JSON structure is already standard in this app likely?
    # Actually, the existing `search_media` endpoint didn't take generic filters.
    # The frontend Likely sends query params or uses a body for POST?
    # Looking at `FilterEngine.parse_filters`, it seems designed for internal use.
    # Let's support the generic filter JSON strings as the most flexible way.
    
    return await local_discover_service.discover_movies(
        page=page,
        filters=parsed_filters,
        sort_by=sort_by
    )
