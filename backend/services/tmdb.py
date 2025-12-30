import httpx
from typing import Optional, List, Dict, Any
from config import get_settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class TMDBService:
    """Service for interacting with TMDB API."""
    
    def __init__(self):
        self.api_key = settings.tmdb_api_key
        self.base_url = settings.tmdb_base_url
        self.image_base_url = settings.tmdb_image_base_url
        self._client: Optional[httpx.AsyncClient] = None
        self._genres_cache: Dict[str, Dict[int, str]] = {}
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                params={"api_key": self.api_key},
                timeout=30.0,
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an API request."""
        client = await self._get_client()
        try:
            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"TMDB API error: {e}")
            raise
    
    # ============ Genre Methods ============
    
    async def get_genres(self, media_type: str = "movie") -> Dict[int, str]:
        """Get genre mapping (id -> name)."""
        if media_type in self._genres_cache:
            return self._genres_cache[media_type]
        
        endpoint = f"/genre/{media_type}/list"
        data = await self._request("GET", endpoint)
        
        genres = {g["id"]: g["name"] for g in data.get("genres", [])}
        self._genres_cache[media_type] = genres
        return genres
    
    # ============ Search Methods ============
    
    async def search(
        self,
        query: str,
        media_type: str = "movie",
        page: int = 1,
        year: Optional[int] = None,
    ) -> Dict:
        """Search for movies or TV shows."""
        endpoint = f"/search/{media_type}"
        params = {"query": query, "page": page}
        
        if year:
            params["year" if media_type == "movie" else "first_air_date_year"] = year
        
        return await self._request("GET", endpoint, params=params)
    
    async def multi_search(self, query: str, page: int = 1) -> Dict:
        """Search for movies, TV shows, and people."""
        return await self._request(
            "GET", "/search/multi",
            params={"query": query, "page": page}
        )
    
    async def find_by_external_id(self, external_id: str, source: str = "imdb_id") -> Dict:
        """Find media by external ID (e.g. IMDb ID)."""
        endpoint = f"/find/{external_id}"
        return await self._request(
            "GET", endpoint,
            params={"external_source": source}
        )
    
    # ============ Discover Methods ============
    
    async def discover(
        self,
        media_type: str = "movie",
        page: int = 1,
        **filters
    ) -> Dict:
        """Discover movies or TV shows with filters."""
        endpoint = f"/discover/{media_type}"
        params = {"page": page, **filters}
        return await self._request("GET", endpoint, params=params)
    
    # ============ Detail Methods ============
    
    async def get_details(
        self,
        tmdb_id: int,
        media_type: str = "movie",
        append_to_response: Optional[str] = None,
    ) -> Dict:
        """Get detailed information about a movie or TV show."""
        endpoint = f"/{media_type}/{tmdb_id}"
        params = {}
        
        if append_to_response is None:
            append_to_response = "credits,keywords,watch/providers,external_ids"
        params["append_to_response"] = append_to_response
        
        return await self._request("GET", endpoint, params=params)
    
    async def get_external_ids(self, tmdb_id: int, media_type: str = "movie") -> Dict:
        """Get external IDs (IMDB, TVDB, etc.)."""
        endpoint = f"/{media_type}/{tmdb_id}/external_ids"
        return await self._request("GET", endpoint)
    
    async def get_watch_providers(
        self,
        tmdb_id: int,
        media_type: str = "movie",
        region: str = "DE",
    ) -> Dict:
        """Get streaming/watch providers."""
        endpoint = f"/{media_type}/{tmdb_id}/watch/providers"
        data = await self._request("GET", endpoint)
        return data.get("results", {}).get(region, {})
    
    # ============ Trending & Popular ============
    
    async def get_trending(
        self,
        media_type: str = "movie",
        time_window: str = "week",
        page: int = 1,
    ) -> Dict:
        """Get trending movies or TV shows."""
        endpoint = f"/trending/{media_type}/{time_window}"
        return await self._request("GET", endpoint, params={"page": page})
    
    async def get_popular(self, media_type: str = "movie", page: int = 1) -> Dict:
        """Get popular movies or TV shows."""
        endpoint = f"/{media_type}/popular"
        return await self._request("GET", endpoint, params={"page": page})
    
    async def get_top_rated(self, media_type: str = "movie", page: int = 1) -> Dict:
        """Get top rated movies or TV shows."""
        endpoint = f"/{media_type}/top_rated"
        return await self._request("GET", endpoint, params={"page": page})
    
    async def get_upcoming(self, page: int = 1) -> Dict:
        """Get upcoming movies."""
        return await self._request("GET", "/movie/upcoming", params={"page": page})
    
    async def get_now_playing(self, page: int = 1) -> Dict:
        """Get now playing movies."""
        return await self._request("GET", "/movie/now_playing", params={"page": page})
    
    async def get_airing_today(self, page: int = 1) -> Dict:
        """Get TV shows airing today."""
        return await self._request("GET", "/tv/airing_today", params={"page": page})
    
    # ============ Helper Methods ============
    
    def get_image_url(
        self,
        path: Optional[str],
        size: str = "w500",
    ) -> Optional[str]:
        """Get full image URL from path."""
        if not path:
            return None
        return f"{self.image_base_url}/{size}{path}"
    
    def normalize_result(self, item: Dict, media_type: str = "movie") -> Dict:
        """Normalize TMDB result to consistent format."""
        return {
            "tmdb_id": item.get("id"),
            "media_type": media_type,
            "title": item.get("title") or item.get("name"),
            "original_title": item.get("original_title") or item.get("original_name"),
            "poster_path": item.get("poster_path"),
            "backdrop_path": item.get("backdrop_path"),
            "overview": item.get("overview"),
            "release_date": item.get("release_date") or item.get("first_air_date"),
            "vote_average": item.get("vote_average"),
            "vote_count": item.get("vote_count"),
            "popularity": item.get("popularity"),
            "genre_ids": item.get("genre_ids", []),
        }


# Singleton instance
tmdb_service = TMDBService()
