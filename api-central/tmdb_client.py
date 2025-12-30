import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, List
from config import TMDB_API_KEY, TMDB_BASE_URL, RATE_LIMIT_REQUESTS, RATE_LIMIT_PERIOD

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_period: int, period_seconds: int):
        self.requests_per_period = requests_per_period
        self.period_seconds = period_seconds
        self.request_times: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until we can make another request."""
        while True:
            async with self._lock:
                now = asyncio.get_event_loop().time()
                
                # Cleanup old requests
                self.request_times = [t for t in self.request_times if now - t < self.period_seconds]

                if len(self.request_times) < self.requests_per_period:
                    self.request_times.append(now)
                    return  # Access granted immediately
                
                # Calculate wait time based on the oldest request
                wait_time = self.request_times[0] + self.period_seconds - now
            
            # Sleep OUTSIDE the lock
            if wait_time > 0:
                await asyncio.sleep(wait_time + 0.05)  # slight buffer


class TMDBClient:
    """Async TMDB API client with rate limiting and full data fetching."""

    def __init__(self):
        self.base_url = TMDB_BASE_URL
        self.api_key = TMDB_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_PERIOD)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make a rate-limited API request."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        await self.rate_limiter.acquire()

        url = f"{self.base_url}{endpoint}"
        request_params = {"api_key": self.api_key}
        if params:
            request_params.update(params)

        try:
            async with self.session.get(url, params=request_params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get("Retry-After", 10))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    return await self._request(endpoint, params)
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"API error {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            return None

    # ============ Discovery Endpoints ============

    async def discover_movies(self, page: int = 1) -> Optional[Dict]:
        """Get a page of movies from discover endpoint."""
        return await self._request("/discover/movie", {
            "page": page,
            "sort_by": "popularity.desc",
            "include_adult": "true",
            "include_video": "true",
        })

    async def discover_tv(self, page: int = 1) -> Optional[Dict]:
        """Get a page of TV shows from discover endpoint."""
        return await self._request("/discover/tv", {
            "page": page,
            "sort_by": "popularity.desc",
            "include_adult": "true",
        })

    # ============ Movie Details ============

    async def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """Get full movie details with all appended data."""
        return await self._request(f"/movie/{movie_id}", {
            "append_to_response": "credits,keywords,videos,watch/providers,release_dates,alternative_titles,recommendations,similar,external_ids"
        })

    async def get_movie_external_ids(self, movie_id: int) -> Optional[Dict]:
        """Get external IDs (IMDB, etc.) for a movie."""
        return await self._request(f"/movie/{movie_id}/external_ids")

    # ============ TV Show Details ============

    async def get_tv_details(self, tv_id: int) -> Optional[Dict]:
        """Get full TV show details with all appended data."""
        return await self._request(f"/tv/{tv_id}", {
            "append_to_response": "credits,keywords,videos,watch/providers,content_ratings,alternative_titles,recommendations,similar"
        })

    async def get_tv_external_ids(self, tv_id: int) -> Optional[Dict]:
        """Get external IDs (IMDB, TVDB, etc.) for a TV show."""
        return await self._request(f"/tv/{tv_id}/external_ids")

    # ============ Reference Data ============

    async def get_movie_genres(self) -> Optional[Dict]:
        """Get all movie genres."""
        return await self._request("/genre/movie/list")

    async def get_tv_genres(self) -> Optional[Dict]:
        """Get all TV genres."""
        return await self._request("/genre/tv/list")

    async def get_watch_providers_movie(self) -> Optional[Dict]:
        """Get all movie watch providers."""
        return await self._request("/watch/providers/movie")

    async def get_watch_providers_tv(self) -> Optional[Dict]:
        """Get all TV watch providers."""
        return await self._request("/watch/providers/tv")

    # ============ Helper Methods ============

    def parse_movie_data(self, basic_data: Dict, details: Dict, external_ids: Dict) -> Dict:
        """Parse and combine movie data into database format."""
        # Extract directors from crew
        directors = []
        if details and "credits" in details:
            crew = details.get("credits", {}).get("crew", [])
            directors = [
                {"id": c["id"], "name": c["name"]}
                for c in crew if c.get("job") == "Director"
            ]

        # Get top cast (limit to 20)
        cast = []
        if details and "credits" in details:
            cast = [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "character": c.get("character"),
                    "order": c.get("order"),
                }
                for c in details.get("credits", {}).get("cast", [])[:20]
            ]

        # Get keywords
        keywords = []
        if details and "keywords" in details:
            keywords = details.get("keywords", {}).get("keywords", [])

        # Get videos (trailers)
        videos = []
        if details and "videos" in details:
            videos = [
                {
                    "key": v["key"],
                    "name": v["name"],
                    "type": v["type"],
                    "site": v["site"],
                }
                for v in details.get("videos", {}).get("results", [])
                if v.get("site") == "YouTube"
            ]

        # Get watch providers
        watch_providers = {}
        if details and "watch/providers" in details:
            watch_providers = details.get("watch/providers", {}).get("results", {})

        # Get release dates and certifications
        release_dates = {}
        certifications = {}
        if details and "release_dates" in details:
            for result in details.get("release_dates", {}).get("results", []):
                region = result.get("iso_3166_1")
                release_dates[region] = result.get("release_dates", [])
                # Extract certification
                for rd in result.get("release_dates", []):
                    if rd.get("certification"):
                        certifications[region] = rd["certification"]
                        break

        # Get alternative titles
        alternative_titles = []
        if details and "alternative_titles" in details:
            alternative_titles = details.get("alternative_titles", {}).get("titles", [])

        # Get recommendations
        recommendations = []
        if details and "recommendations" in details:
            recommendations = [
                r["id"] for r in details.get("recommendations", {}).get("results", [])
            ]

        # Get similar
        similar = []
        if details and "similar" in details:
            similar = [
                s["id"] for s in details.get("similar", {}).get("results", [])
            ]

        return {
            "id": basic_data.get("id"),
            "imdb_id": external_ids.get("imdb_id") if external_ids else None,
            "title": basic_data.get("title"),
            "original_title": basic_data.get("original_title"),
            "original_language": basic_data.get("original_language"),
            "overview": basic_data.get("overview"),
            "tagline": details.get("tagline") if details else None,
            "release_date": basic_data.get("release_date"),
            "status": details.get("status") if details else None,
            "vote_average": basic_data.get("vote_average"),
            "vote_count": basic_data.get("vote_count"),
            "popularity": basic_data.get("popularity"),
            "runtime": details.get("runtime") if details else None,
            "budget": details.get("budget") if details else None,
            "revenue": details.get("revenue") if details else None,
            "poster_path": basic_data.get("poster_path"),
            "backdrop_path": basic_data.get("backdrop_path"),
            "genres": basic_data.get("genre_ids") if "genre_ids" in basic_data else details.get("genres") if details else None,
            "production_countries": details.get("production_countries") if details else None,
            "production_companies": details.get("production_companies") if details else None,
            "spoken_languages": details.get("spoken_languages") if details else None,
            "keywords": keywords,
            "cast": cast,
            "crew": details.get("credits", {}).get("crew", [])[:10] if details and "credits" in details else None,
            "directors": directors,
            "watch_providers": watch_providers,
            "release_dates": release_dates,
            "certifications": certifications,
            "alternative_titles": alternative_titles,
            "videos": videos,
            "recommendations": recommendations,
            "similar": similar,
            "belongs_to_collection": details.get("belongs_to_collection") if details else None,
            "adult": basic_data.get("adult", False),
            "video": basic_data.get("video", False),
            "homepage": details.get("homepage") if details else None,
        }

    def parse_tv_data(self, basic_data: Dict, details: Dict, external_ids: Dict) -> Dict:
        """Parse and combine TV show data into database format."""
        # Get top cast (limit to 20)
        cast = []
        if details and "credits" in details:
            cast = [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "character": c.get("character"),
                    "order": c.get("order"),
                }
                for c in details.get("credits", {}).get("cast", [])[:20]
            ]

        # Get keywords
        keywords = []
        if details and "keywords" in details:
            keywords = details.get("keywords", {}).get("results", [])

        # Get videos (trailers)
        videos = []
        if details and "videos" in details:
            videos = [
                {
                    "key": v["key"],
                    "name": v["name"],
                    "type": v["type"],
                    "site": v["site"],
                }
                for v in details.get("videos", {}).get("results", [])
                if v.get("site") == "YouTube"
            ]

        # Get watch providers
        watch_providers = {}
        if details and "watch/providers" in details:
            watch_providers = details.get("watch/providers", {}).get("results", {})

        # Get content ratings
        content_ratings = {}
        if details and "content_ratings" in details:
            for result in details.get("content_ratings", {}).get("results", []):
                region = result.get("iso_3166_1")
                content_ratings[region] = result.get("rating")

        # Get alternative titles
        alternative_titles = []
        if details and "alternative_titles" in details:
            alternative_titles = details.get("alternative_titles", {}).get("results", [])

        # Get recommendations
        recommendations = []
        if details and "recommendations" in details:
            recommendations = [
                r["id"] for r in details.get("recommendations", {}).get("results", [])
            ]

        # Get similar
        similar = []
        if details and "similar" in details:
            similar = [
                s["id"] for s in details.get("similar", {}).get("results", [])
            ]

        return {
            "id": basic_data.get("id"),
            "imdb_id": external_ids.get("imdb_id") if external_ids else None,
            "tvdb_id": external_ids.get("tvdb_id") if external_ids else None,
            "name": basic_data.get("name"),
            "original_name": basic_data.get("original_name"),
            "original_language": basic_data.get("original_language"),
            "overview": basic_data.get("overview"),
            "tagline": details.get("tagline") if details else None,
            "first_air_date": basic_data.get("first_air_date"),
            "last_air_date": details.get("last_air_date") if details else None,
            "next_episode_to_air": details.get("next_episode_to_air") if details else None,
            "last_episode_to_air": details.get("last_episode_to_air") if details else None,
            "status": details.get("status") if details else None,
            "type": details.get("type") if details else None,
            "vote_average": basic_data.get("vote_average"),
            "vote_count": basic_data.get("vote_count"),
            "popularity": basic_data.get("popularity"),
            "number_of_seasons": details.get("number_of_seasons") if details else None,
            "number_of_episodes": details.get("number_of_episodes") if details else None,
            "episode_run_time": details.get("episode_run_time") if details else None,
            "seasons": details.get("seasons") if details else None,
            "poster_path": basic_data.get("poster_path"),
            "backdrop_path": basic_data.get("backdrop_path"),
            "genres": basic_data.get("genre_ids") if "genre_ids" in basic_data else details.get("genres") if details else None,
            "production_countries": details.get("production_countries") if details else None,
            "production_companies": details.get("production_companies") if details else None,
            "spoken_languages": details.get("spoken_languages") if details else None,
            "networks": details.get("networks") if details else None,
            "origin_country": basic_data.get("origin_country"),
            "keywords": keywords,
            "cast": cast,
            "crew": details.get("credits", {}).get("crew", [])[:10] if details and "credits" in details else None,
            "created_by": details.get("created_by") if details else None,
            "watch_providers": watch_providers,
            "content_ratings": content_ratings,
            "alternative_titles": alternative_titles,
            "videos": videos,
            "recommendations": recommendations,
            "similar": similar,
            "adult": basic_data.get("adult", False),
            "in_production": details.get("in_production", False) if details else False,
            "homepage": details.get("homepage") if details else None,
        }


# Global client instance
tmdb_client = TMDBClient()
