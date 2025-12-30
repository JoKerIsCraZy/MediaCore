from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from services.tmdb import tmdb_service
from services.filter_engine import AVAILABLE_FILTERS, SORT_OPTIONS_LIST
from services.local_discover import local_discover_service
import asyncio

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
            
    # Enrich with IMDb ratings (if available in local DB)
    if normalized:
        normalized = await local_discover_service.enrich_movies_with_ratings(normalized)
    
    return {
        "results": normalized,
        "page": result.get("page", 1),
        "total_pages": result.get("total_pages", 0),
        "total_results": result.get("total_results", 0),
    }


# Helper for multi-page fetching (3 TMDB pages = 1 App page -> 60 items)
async def fetch_multi_page(fetch_func, *args, page: int = 1, media_type: str = "movie"):
    tmdb_results = []
    total_pages = 0
    total_results = 0
    
    # Fetch 3 pages
    start_page = (page - 1) * 3 + 1
    import asyncio
    
    # Prepare tasks
    tasks = []
    for p in range(start_page, start_page + 3):
        tasks.append(fetch_func(*args, page=p))
        
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for response in responses:
        if isinstance(response, dict):
            # Aggregate stats from the first successful response (approximate)
            if not total_results:
                total_results = response.get("total_results", 0)
                # Adjust total pages by factor of 3
                orig_total = response.get("total_pages", 0)
                total_pages = (orig_total + 2) // 3
            
            items = response.get("results", [])
            for item in items:
                tmdb_results.append(tmdb_service.normalize_result(item, media_type))
        else:
            # Handle error or exception
            pass
            
    return {
        "results": tmdb_results,
        "page": page,
        "total_pages": total_pages,
        "total_results": total_results
    }


@router.get("/trending")
async def get_trending(
    media_type: str = Query("movie", regex="^(movie|tv)$"),
    time_window: str = Query("week", regex="^(day|week)$"),
    page: int = Query(1, ge=1),
):
    """Get trending movies or TV shows (60 items per page)."""
    data = await fetch_multi_page(tmdb_service.get_trending, media_type, time_window, page=page, media_type=media_type)
    
    if data["results"]:
        data["results"] = await local_discover_service.enrich_movies_with_ratings(data["results"])
    
    return data


@router.get("/popular")
async def get_popular(
    media_type: str = Query("movie", regex="^(movie|tv)$"),
    page: int = Query(1, ge=1),
):
    """Get popular movies or TV shows (60 items per page)."""
    data = await fetch_multi_page(tmdb_service.get_popular, media_type, page=page, media_type=media_type)
    
    if data["results"]:
        data["results"] = await local_discover_service.enrich_movies_with_ratings(data["results"])
    
    return data


@router.get("/top-rated")
async def get_top_rated(
    media_type: str = Query("movie", regex="^(movie|tv)$"),
    page: int = Query(1, ge=1),
):
    """Get top rated movies or TV shows (60 items per page)."""
    data = await fetch_multi_page(tmdb_service.get_top_rated, media_type, page=page, media_type=media_type)
    
    if data["results"]:
        data["results"] = await local_discover_service.enrich_movies_with_ratings(data["results"])
    
    return data


@router.get("/upcoming")
async def get_upcoming(page: int = Query(1, ge=1)):
    """Get upcoming movies (60 items per page)."""
    # upcoming is movie only
    data = await fetch_multi_page(tmdb_service.get_upcoming, page=page, media_type="movie")
    
    if data["results"]:
        data["results"] = await local_discover_service.enrich_movies_with_ratings(data["results"])
    
    return data


@router.get("/now-playing")
async def get_now_playing(page: int = Query(1, ge=1)):
    """Get movies currently in theaters (60 items per page)."""
    data = await fetch_multi_page(tmdb_service.get_now_playing, page=page, media_type="movie")
    
    if data["results"]:
        data["results"] = await local_discover_service.enrich_movies_with_ratings(data["results"])
    
    return data


@router.get("/airing-today")
async def get_airing_today(page: int = Query(1, ge=1)):
    """Get TV shows airing today (60 items per page)."""
    data = await fetch_multi_page(tmdb_service.get_airing_today, page=page, media_type="tv")
    
    if data["results"]:
        data["results"] = await local_discover_service.enrich_movies_with_ratings(data["results"])
    
    return data


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
    
    # Enrichment: Fetch IMDb Rating if imdb_id exists
    if result.get("imdb_id"):
        try:
            from database import media_session_factory
            from models_media import ImdbRating
            from sqlalchemy import select
            
            async with media_session_factory() as session:
                stmt_r = select(ImdbRating.averageRating, ImdbRating.numVotes).where(ImdbRating.tconst == result["imdb_id"])
                rr = await session.execute(stmt_r)
                row = rr.first()
                if row:
                    result["imdb_rating"] = row.averageRating
                    result["imdb_votes"] = row.numVotes
        except Exception as e:
            # log but don't fail
            pass
    
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
