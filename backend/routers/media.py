from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from services.tmdb import tmdb_service
from services.filter_engine import AVAILABLE_FILTERS, SORT_OPTIONS_LIST

router = APIRouter(prefix="/media", tags=["Media"])


@router.get("/search")
async def search_media(
    query: str = Query(..., min_length=1),
    media_type: str = Query("movie", regex="^(movie|tv|multi)$"),
    page: int = Query(1, ge=1),
    year: Optional[int] = None,
):
    """Search for movies or TV shows."""
    if media_type == "multi":
        result = await tmdb_service.multi_search(query, page)
    else:
        result = await tmdb_service.search(query, media_type, page, year)
    
    # Normalize results
    normalized = []
    for item in result.get("results", []):
        item_type = item.get("media_type", media_type)
        if item_type in ["movie", "tv"]:
            normalized.append(tmdb_service.normalize_result(item, item_type))
    
    return {
        "results": normalized,
        "page": result.get("page", 1),
        "total_pages": result.get("total_pages", 0),
        "total_results": result.get("total_results", 0),
    }


@router.get("/trending")
async def get_trending(
    media_type: str = Query("movie", regex="^(movie|tv)$"),
    time_window: str = Query("week", regex="^(day|week)$"),
    page: int = Query(1, ge=1),
):
    """Get trending movies or TV shows."""
    result = await tmdb_service.get_trending(media_type, time_window, page)
    
    normalized = [
        tmdb_service.normalize_result(item, media_type)
        for item in result.get("results", [])
    ]
    
    return {
        "results": normalized,
        "page": result.get("page", 1),
        "total_pages": result.get("total_pages", 0),
        "total_results": result.get("total_results", 0),
    }


@router.get("/popular")
async def get_popular(
    media_type: str = Query("movie", regex="^(movie|tv)$"),
    page: int = Query(1, ge=1),
):
    """Get popular movies or TV shows."""
    result = await tmdb_service.get_popular(media_type, page)
    
    normalized = [
        tmdb_service.normalize_result(item, media_type)
        for item in result.get("results", [])
    ]
    
    return {
        "results": normalized,
        "page": result.get("page", 1),
        "total_pages": result.get("total_pages", 0),
        "total_results": result.get("total_results", 0),
    }


@router.get("/top-rated")
async def get_top_rated(
    media_type: str = Query("movie", regex="^(movie|tv)$"),
    page: int = Query(1, ge=1),
):
    """Get top rated movies or TV shows."""
    result = await tmdb_service.get_top_rated(media_type, page)
    
    normalized = [
        tmdb_service.normalize_result(item, media_type)
        for item in result.get("results", [])
    ]
    
    return {
        "results": normalized,
        "page": result.get("page", 1),
        "total_pages": result.get("total_pages", 0),
        "total_results": result.get("total_results", 0),
    }


@router.get("/upcoming")
async def get_upcoming(page: int = Query(1, ge=1)):
    """Get upcoming movies."""
    result = await tmdb_service.get_upcoming(page)
    
    normalized = [
        tmdb_service.normalize_result(item, "movie")
        for item in result.get("results", [])
    ]
    
    return {
        "results": normalized,
        "page": result.get("page", 1),
        "total_pages": result.get("total_pages", 0),
        "total_results": result.get("total_results", 0),
    }


@router.get("/now-playing")
async def get_now_playing(page: int = Query(1, ge=1)):
    """Get movies currently in theaters."""
    result = await tmdb_service.get_now_playing(page)
    
    normalized = [
        tmdb_service.normalize_result(item, "movie")
        for item in result.get("results", [])
    ]
    
    return {
        "results": normalized,
        "page": result.get("page", 1),
        "total_pages": result.get("total_pages", 0),
        "total_results": result.get("total_results", 0),
    }


@router.get("/airing-today")
async def get_airing_today(page: int = Query(1, ge=1)):
    """Get TV shows airing today."""
    result = await tmdb_service.get_airing_today(page)
    
    normalized = [
        tmdb_service.normalize_result(item, "tv")
        for item in result.get("results", [])
    ]
    
    return {
        "results": normalized,
        "page": result.get("page", 1),
        "total_pages": result.get("total_pages", 0),
        "total_results": result.get("total_results", 0),
    }


@router.get("/{media_type}/{tmdb_id}")
async def get_media_details(
    media_type: str,
    tmdb_id: int,
):
    """Get detailed information about a movie or TV show."""
    if media_type not in ["movie", "tv"]:
        raise HTTPException(status_code=400, detail="Invalid media type")
    
    try:
        details = await tmdb_service.get_details(tmdb_id, media_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Extract relevant data
    result = tmdb_service.normalize_result(details, media_type)
    
    # Add additional details
    result["genres"] = details.get("genres", [])
    result["runtime"] = details.get("runtime") or details.get("episode_run_time", [None])[0] if details.get("episode_run_time") else None
    result["status"] = details.get("status")
    result["tagline"] = details.get("tagline")
    result["budget"] = details.get("budget")
    result["revenue"] = details.get("revenue")
    
    # External IDs
    external_ids = details.get("external_ids", {})
    result["imdb_id"] = external_ids.get("imdb_id")
    result["tvdb_id"] = external_ids.get("tvdb_id")
    
    # Keywords
    keywords_data = details.get("keywords", {})
    keywords = keywords_data.get("keywords") or keywords_data.get("results", [])
    result["keywords"] = [k["name"] for k in keywords]
    
    # Cast & Crew (top 10)
    credits = details.get("credits", {})
    result["cast"] = [
        {"name": p["name"], "character": p.get("character"), "profile_path": p.get("profile_path")}
        for p in credits.get("cast", [])[:10]
    ]
    result["crew"] = [
        {"name": p["name"], "job": p.get("job"), "department": p.get("department")}
        for p in credits.get("crew", [])
        if p.get("job") in ["Director", "Writer", "Screenplay", "Producer"]
    ][:5]
    
    # Watch providers
    watch_providers = details.get("watch/providers", {}).get("results", {})
    result["watch_providers"] = watch_providers.get("DE", {})  # Germany as default
    
    return result


# ============ Metadata Endpoints ============

@router.get("/genres/{media_type}")
async def get_genres(media_type: str):
    """Get available genres for a media type."""
    if media_type not in ["movie", "tv"]:
        raise HTTPException(status_code=400, detail="Invalid media type")
    
    genres = await tmdb_service.get_genres(media_type)
    return [{"id": k, "name": v} for k, v in genres.items()]


@router.get("/filters")
async def get_available_filters():
    """Get available filter options for the filter builder."""
    return AVAILABLE_FILTERS


@router.get("/sort-options")
async def get_sort_options():
    """Get available sort options."""
    return SORT_OPTIONS_LIST
