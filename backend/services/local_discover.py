from sqlalchemy import select, desc, asc, func, or_, and_
from sqlalchemy.orm import selectinload
from database import get_db, media_session_factory
from models_media import Movie, ImdbRating, Genre
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LocalDiscoverService:
    def __init__(self):
        pass

    async def discover_movies(
        self,
        page: int = 1,
        filters: List[Dict[str, Any]] = None,
        sort_by: str = "popularity.desc",
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Discover movies using Hybrid Approach:
        1. Query IMDb tables first (reliable data source).
        2. Resolve to TMDB data (local DB first, then API on-demand).
        """
        filters = filters or []
        offset = (page - 1) * limit
        
        async with media_session_factory() as session:
            # 1. Query IMDb IDs directly from Ratings table
            # We join with ImdbTitles if we need title search or genre filters (in future)
            # CHANGE: Fetch rating info too
            stmt = select(ImdbRating.tconst, ImdbRating.averageRating, ImdbRating.numVotes).select_from(ImdbRating)
            
            # Apply Filters (IMDb specific)
            stmt = self._apply_filters_imdb(stmt, filters)
            
            # Apply Sorting (IMDb specific)
            stmt = self._apply_sorting_imdb(stmt, sort_by)
            
            # Count total (approximate or separate count query)
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_results = (await session.execute(count_stmt)).scalar() or 0
            
            # Apply Pagination
            stmt = stmt.offset(offset).limit(limit)
            
            # Execute to get IMDb IDs and Ratings
            result = await session.execute(stmt)
            rows = result.all() # list of (tconst, averageRating, numVotes)
            
            if not rows:
                 return {"results": [], "page": page, "total_pages": 0, "total_results": 0}
            
            # Create map for ratings
            imdb_data_map = {row.tconst: {"imdb_rating": row.averageRating, "imdb_votes": row.numVotes} for row in rows}
            imdb_ids = list(imdb_data_map.keys())

            # 2. Resolve to Movies
            # a) Check local 'movies' table
            stmt_movies = select(Movie).where(Movie.imdb_id.in_(imdb_ids))
            result_movies = await session.execute(stmt_movies)
            local_movies = {m.imdb_id: m for m in result_movies.scalars().all()}
            
            final_results = []
            
            # b) For each ID, get content (Local or API)
            # Implemented with asyncio.gather for parallelism if we fetch API
            from services.tmdb import tmdb_service
            import asyncio
            
            async def fetch_missing(tconst):
                # Try to fetch from TMDB API
                try:
                    data = await tmdb_service.find_by_external_id(tconst, source="imdb_id")
                    results = data.get("movie_results", [])
                    if results:
                        # Normalize one result
                        tmdb_data = results[0]
                        normalized = tmdb_service.normalize_result(tmdb_data)
                        # CRITICAL: Ensure imdb_id is preserved so we can map it back!
                        normalized["imdb_id"] = tconst
                        return normalized
                except Exception as e:
                    logger.error(f"Failed to fetch {tconst} from TMDB: {e}")
                return None

            tasks = []
            for tconst in imdb_ids:
                if tconst in local_movies:
                    # Use local data
                    final_results.append(self._normalize_movie(local_movies[tconst]))
                else:
                    # Need to fetch
                    tasks.append(fetch_missing(tconst))
            
            if tasks:
                logger.info(f"Fetching {len(tasks)} items from TMDB API on-the-fly...")
                api_results = await asyncio.gather(*tasks)
                
                # Filter None and Cache results
                new_movies_to_cache = []
                for res in api_results:
                    if res:
                         final_results.append(res)
                         # Prepare for caching
                         new_movies_to_cache.append(res)
                
                # CACHE: Save newly fetched movies to DB to prevent re-fetching
                if new_movies_to_cache:
                    try:
                        for m_data in new_movies_to_cache:
                            # Check if exists (concurrency safety)
                            existing = await session.get(Movie, m_data["tmdb_id"])
                            if not existing:
                                # Map dict to Movie model
                                # Use default values for missing fields to avoid errors
                                new_movie = Movie(
                                    id=m_data["tmdb_id"],
                                    imdb_id=m_data.get("imdb_id"),
                                    title=m_data.get("title") or "Unknown",
                                    original_title=m_data.get("original_title"),
                                    overview=m_data.get("overview"),
                                    poster_path=m_data.get("poster_path"),
                                    backdrop_path=m_data.get("backdrop_path"),
                                    release_date=m_data.get("release_date"),
                                    vote_average=m_data.get("vote_average"),
                                    vote_count=m_data.get("vote_count"),
                                    popularity=m_data.get("popularity"),
                                    # media_type="movie"  <-- REMOVED: invalid argument for Movie model
                                )
                                session.add(new_movie)
                        await session.commit()
                        logger.info(f"Cached {len(new_movies_to_cache)} movies to local DB")
                    except Exception as e:
                        logger.error(f"Failed to cache movies: {e}")
                        await session.rollback()

            # Sort final results to match original order of imdb_ids AND INJECT RATINGS
            # (Fetching async might scramble order, dictionary lookup is fine)
            # We want to preserve 'imdb_ids' order.
            
            ordered_results = []
            
            def get_imdb_id(item):
                if isinstance(item, dict): return item.get("imdb_id")
                return item.imdb_id
                
            lookup = {get_imdb_id(m): m for m in final_results}
            
            for tconst in imdb_ids:
                if tconst in lookup:
                     item = lookup[tconst]
                     # If it's ORM, normalize it now
                     if not isinstance(item, dict):
                         item = self._normalize_movie(item)
                     
                     # INJECT IMDB DATA
                     if tconst in imdb_data_map:
                         item.update(imdb_data_map[tconst])
                         
                     ordered_results.append(item)

            total_pages = (total_results + limit - 1) // limit
            
            return {
                "results": ordered_results,
                "page": page,
                "total_pages": total_pages,
                "total_results": total_results
            }

    def _apply_filters_imdb(self, stmt, filters):
        for f in filters:
            field = f.get("field")
            op = f.get("operator", "eq")
            value = f.get("value")
            
            if value is None: continue
                
            if field == "imdb_rating":
                if op == "gte": stmt = stmt.where(ImdbRating.averageRating >= float(value))
                elif op == "lte": stmt = stmt.where(ImdbRating.averageRating <= float(value))
            elif field == "imdb_votes":
                if op == "gte": stmt = stmt.where(ImdbRating.numVotes >= int(value))
        return stmt

    def _apply_sorting_imdb(self, stmt, sort_by):
        # Default to popularity? IMDb doesn't have popularity column in Ratings.
        # It has numVotes which is a proxy for popularity.
        if sort_by == "popularity.desc":
            return stmt.order_by(ImdbRating.numVotes.desc().nulls_last())
        elif sort_by == "imdb_rating.desc":
            return stmt.order_by(ImdbRating.averageRating.desc().nulls_last())
        elif sort_by == "imdb_rating.asc":
            return stmt.order_by(ImdbRating.averageRating.asc().nulls_last())
        return stmt.order_by(ImdbRating.numVotes.desc())

    def _normalize_movie(self, movie: Movie) -> Dict:
        """Convert DB model to frontend friendly dict"""
        return {
            "id": movie.id,
            "tmdb_id": movie.id,
            "imdb_id": movie.imdb_id,
            "title": movie.title,
            "original_title": movie.original_title,
            "overview": movie.overview,
            "poster_path": movie.poster_path,
            "backdrop_path": movie.backdrop_path,
            "release_date": movie.release_date,
            "vote_average": movie.vote_average,
            "vote_count": movie.vote_count,
            "popularity": movie.popularity,
            "media_type": "movie",
        }

    async def enrich_movies_with_ratings(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich a list of normalized movie objects with IMDb ratings from local DB.
        This relies on the 'movies' table being populated to link TMDB ID -> IMDb ID.
        """
        if not movies:
            return movies
            
        tmdb_ids = [m["tmdb_id"] for m in movies if m.get("tmdb_id")]
        if not tmdb_ids:
            return movies
            
        async with media_session_factory() as session:
            # 0. Check which items ALREADY have imdb_id
            tmdb_to_imdb = {}
            movies_map = {m["tmdb_id"]: m for m in movies}
            
            for m in movies:
                tid = m.get("tmdb_id")
                iid = m.get("imdb_id")
                if tid and iid:
                    tmdb_to_imdb[tid] = iid

            # 1. Get IMDb IDs for the REST from local movies table
            missing_tmdb_ids = [tid for tid in tmdb_ids if tid not in tmdb_to_imdb]
            
            if missing_tmdb_ids:
                stmt = select(Movie.id, Movie.imdb_id).where(Movie.id.in_(missing_tmdb_ids))
                result = await session.execute(stmt)
                for row in result.all():
                    if row.imdb_id:
                        tmdb_to_imdb[row.id] = row.imdb_id
            
            # FALLBACK: If we still have missing IDs, fetch from TMDB API live
            still_missing = [tid for tid in tmdb_ids if tid not in tmdb_to_imdb]
            
            if still_missing:
                from services.tmdb import tmdb_service
                import asyncio
                
                async def fetch_imdb_id(tid):
                    try:
                        # Try to get external IDs
                        # Note: we assume 'movie' as default or checking list item type?
                        # Enriched items have "media_type"
                        m_type = next((m.get("media_type", "movie") for m in movies if m.get("tmdb_id") == tid), "movie")
                        ext_ids = await tmdb_service.get_external_ids(tid, m_type)
                        return (tid, ext_ids.get("imdb_id"))
                    except Exception as e:
                        # logger.warning(f"Failed to fetch external ID for {tid}: {e}")
                        return (tid, None)

                # Fetch in parallel
                tasks = [fetch_imdb_id(tid) for tid in still_missing]
                if tasks:
                    fetched_results = await asyncio.gather(*tasks)
                    
                    new_mappings_to_cache = []
                    
                    for tid, iid in fetched_results:
                        if iid:
                            tmdb_to_imdb[tid] = iid
                            # Prepare to cache this new mapping!
                            # We can create a Movie object if we have data from 'movies_map'
                            if tid in movies_map:
                                m_data = movies_map[tid]
                                new_mappings_to_cache.append({
                                    "tmdb_id": tid, 
                                    "imdb_id": iid,
                                    "data": m_data
                                })

                    # CACHE: Save newly discovered IDs to Movie table
                    if new_mappings_to_cache:
                        try:
                             for item in new_mappings_to_cache:
                                 tid = item["tmdb_id"]
                                 iid = item["imdb_id"]
                                 m_data = item["data"]
                                 
                                 # concurrency check
                                 existing = await session.get(Movie, tid)
                                 if not existing:
                                     new_movie = Movie(
                                        id=tid,
                                        imdb_id=iid,
                                        title=m_data.get("title") or "Unknown",
                                        original_title=m_data.get("original_title"),
                                        overview=m_data.get("overview"),
                                        poster_path=m_data.get("poster_path"),
                                        backdrop_path=m_data.get("backdrop_path"),
                                        release_date=m_data.get("release_date"),
                                        vote_average=m_data.get("vote_average"),
                                        vote_count=m_data.get("vote_count"),
                                        popularity=m_data.get("popularity"),
                                     )
                                     session.add(new_movie)
                                 elif existing and not existing.imdb_id:
                                     # Update existing movie with ID if missing
                                     existing.imdb_id = iid
                                     
                             await session.commit()
                        except Exception as e:
                             logger.error(f"Failed to cache enrichment mappings: {e}")
                             await session.rollback()

            if not tmdb_to_imdb:
                return movies

            imdb_ids = list(tmdb_to_imdb.values())
            
            # 2. Get Ratings for these IMDb IDs
            stmt_ratings = select(ImdbRating.tconst, ImdbRating.averageRating, ImdbRating.numVotes).where(ImdbRating.tconst.in_(imdb_ids))
            result_ratings = await session.execute(stmt_ratings)
            # Map IMDb ID -> Rating
            # Also fetch votes now
            imdb_ratings = {row.tconst: {"rating": row.averageRating, "votes": row.numVotes} for row in result_ratings.all()}
            
            # 3. Attach to movie objects
            for movie in movies:
                tid = movie.get("tmdb_id")
                if tid in tmdb_to_imdb:
                    imdb_id = tmdb_to_imdb[tid]
                    
                    # Ensure imdb_id is set on the object
                    movie["imdb_id"] = imdb_id
                    
                    if imdb_id in imdb_ratings:
                        movie["imdb_rating"] = imdb_ratings[imdb_id]["rating"]
                        movie["imdb_votes"] = imdb_ratings[imdb_id]["votes"]
                        
        return movies

local_discover_service = LocalDiscoverService()
