#!/usr/bin/env python3
"""
TMDB Importer - High-performance parallel data fetcher.

Usage:
    python tmdb_importer.py                    # Full import (movies + tv, detailed)
    python tmdb_importer.py --movies           # Only movies
    python tmdb_importer.py --tv               # Only TV shows
    python tmdb_importer.py --light            # Light mode (basic data only)
    python tmdb_importer.py --pages 100        # Limit to N pages (default: 500)
    python tmdb_importer.py --workers 20       # Parallel workers (default: 20)
    python tmdb_importer.py --batch 5          # Pages per batch (default: 5)
"""

import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Optional

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, close_db, get_session, update_sync_progress, get_sync_progress
from models import Movie, TVShow, Genre, WatchProvider
from tmdb_client import TMDBClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("tmdb_import.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("tmdb_importer")


class TMDBImporter:
    """High-performance TMDB data importer with multi-level parallelism."""

    def __init__(self, light_mode: bool = False, max_pages: int = 500,
                 max_workers: int = 20, pages_per_batch: int = 5):
        self.light_mode = light_mode
        self.max_pages = max_pages
        self.max_workers = max_workers
        self.pages_per_batch = pages_per_batch
        self.client = TMDBClient()
        self.semaphore = asyncio.Semaphore(max_workers)
        self.stats = {
            "movies_processed": 0,
            "movies_failed": 0,
            "tv_processed": 0,
            "tv_failed": 0,
        }
        self._stats_lock = asyncio.Lock()

    async def _increment_stat(self, key: str, amount: int = 1):
        async with self._stats_lock:
            self.stats[key] += amount

    async def import_genres(self):
        """Import all genres from TMDB."""
        logger.info("Importing genres...")
        async with get_session() as session:
            movie_genres, tv_genres = await asyncio.gather(
                self.client.get_movie_genres(),
                self.client.get_tv_genres()
            )
            for genres, media_type in [(movie_genres, "movie"), (tv_genres, "tv")]:
                if genres and "genres" in genres:
                    for g in genres["genres"]:
                        await session.merge(Genre(id=g["id"], name=g["name"], media_type=media_type))
            await session.commit()
        logger.info("Genres imported.")

    async def import_watch_providers(self):
        """Import all watch providers from TMDB."""
        logger.info("Importing watch providers...")
        async with get_session() as session:
            providers_seen = set()
            movie_providers, tv_providers = await asyncio.gather(
                self.client.get_watch_providers_movie(),
                self.client.get_watch_providers_tv()
            )
            for providers in [movie_providers, tv_providers]:
                if providers and "results" in providers:
                    for p in providers["results"]:
                        if p["provider_id"] not in providers_seen:
                            await session.merge(WatchProvider(
                                id=p["provider_id"],
                                name=p["provider_name"],
                                logo_path=p.get("logo_path"),
                                display_priority=p.get("display_priority")
                            ))
                            providers_seen.add(p["provider_id"])
            await session.commit()
        logger.info(f"Imported {len(providers_seen)} watch providers.")

    async def fetch_movie_data(self, movie_basic: dict) -> Optional[dict]:
        """Fetch full movie data with rate limiting."""
        movie_id = movie_basic["id"]
        async with self.semaphore:
            try:
                if self.light_mode:
                    external_ids = await self.client.get_movie_external_ids(movie_id)
                    return {
                        "id": movie_id,
                        "title": movie_basic.get("title"),
                        "original_title": movie_basic.get("original_title"),
                        "original_language": movie_basic.get("original_language"),
                        "overview": movie_basic.get("overview"),
                        "release_date": movie_basic.get("release_date"),
                        "vote_average": movie_basic.get("vote_average"),
                        "vote_count": movie_basic.get("vote_count"),
                        "popularity": movie_basic.get("popularity"),
                        "poster_path": movie_basic.get("poster_path"),
                        "backdrop_path": movie_basic.get("backdrop_path"),
                        "genres": movie_basic.get("genre_ids"),
                        "adult": movie_basic.get("adult", False),
                        "imdb_id": external_ids.get("imdb_id") if external_ids else None,
                    }
                else:
                    details = await self.client.get_movie_details(movie_id)
                    external_ids = details.get("external_ids", {}) if details else {}
                    if not external_ids:
                        external_ids = await self.client.get_movie_external_ids(movie_id) or {}
                    return self.client.parse_movie_data(movie_basic, details, external_ids)
            except Exception as e:
                logger.error(f"Error fetching movie {movie_id}: {e}")
                return None

    async def fetch_tv_data(self, tv_basic: dict) -> Optional[dict]:
        """Fetch full TV data with rate limiting."""
        tv_id = tv_basic["id"]
        async with self.semaphore:
            try:
                if self.light_mode:
                    external_ids = await self.client.get_tv_external_ids(tv_id)
                    return {
                        "id": tv_id,
                        "name": tv_basic.get("name"),
                        "original_name": tv_basic.get("original_name"),
                        "original_language": tv_basic.get("original_language"),
                        "overview": tv_basic.get("overview"),
                        "first_air_date": tv_basic.get("first_air_date"),
                        "vote_average": tv_basic.get("vote_average"),
                        "vote_count": tv_basic.get("vote_count"),
                        "popularity": tv_basic.get("popularity"),
                        "poster_path": tv_basic.get("poster_path"),
                        "backdrop_path": tv_basic.get("backdrop_path"),
                        "genres": tv_basic.get("genre_ids"),
                        "origin_country": tv_basic.get("origin_country"),
                        "adult": tv_basic.get("adult", False),
                        "imdb_id": external_ids.get("imdb_id") if external_ids else None,
                        "tvdb_id": external_ids.get("tvdb_id") if external_ids else None,
                    }
                else:
                    details = await self.client.get_tv_details(tv_id)
                    external_ids = await self.client.get_tv_external_ids(tv_id) or {}
                    return self.client.parse_tv_data(tv_basic, details, external_ids)
            except Exception as e:
                logger.error(f"Error fetching TV {tv_id}: {e}")
                return None

    async def process_page_batch(self, pages: list[int], media_type: str) -> tuple[list[dict], int]:
        """Process multiple pages in parallel."""
        discover_fn = self.client.discover_movies if media_type == "movie" else self.client.discover_tv
        fetch_fn = self.fetch_movie_data if media_type == "movie" else self.fetch_tv_data

        # Fetch all pages in parallel
        page_results = await asyncio.gather(*[discover_fn(page=p) for p in pages])

        # Collect all items from all pages
        all_items = []
        total_pages = 0
        for data in page_results:
            if data and "results" in data:
                all_items.extend(data["results"])
                total_pages = max(total_pages, data.get("total_pages", 0))

        if not all_items:
            return [], total_pages

        # Fetch details for all items in parallel
        results = await asyncio.gather(*[fetch_fn(item) for item in all_items])

        # Filter out None results
        valid_results = [r for r in results if r is not None]
        failed_count = len(results) - len(valid_results)

        return valid_results, total_pages

    async def import_media(self, media_type: str, start_page: int = 1):
        """Import movies or TV shows with batch parallelism."""
        model_class = Movie if media_type == "movie" else TVShow
        stat_key = "movies" if media_type == "movie" else "tv"

        logger.info(f"Starting {media_type} import (pages {start_page}-{self.max_pages}, "
                   f"{'light' if self.light_mode else 'full'} mode, {self.max_workers} workers, "
                   f"{self.pages_per_batch} pages/batch)...")

        # Check for resume point
        async with get_session() as session:
            progress = await get_sync_progress(session, media_type)
            if progress.last_page > 0 and start_page == 1:
                start_page = progress.last_page + 1
                logger.info(f"Resuming from page {start_page}")

        total_pages_discovered = self.max_pages
        current_page = start_page

        while current_page <= min(self.max_pages, total_pages_discovered):
            # Create batch of pages
            batch_end = min(current_page + self.pages_per_batch, self.max_pages + 1)
            pages = list(range(current_page, batch_end))

            logger.info(f"Processing {media_type} pages {pages[0]}-{pages[-1]}...")

            # Process entire batch in parallel
            results, total_pages = await self.process_page_batch(pages, media_type)
            total_pages_discovered = min(total_pages, self.max_pages) if total_pages > 0 else total_pages_discovered

            # Batch save to database
            if results:
                async with get_session() as session:
                    for data in results:
                        await session.merge(model_class(**data))
                    await session.commit()
                    await update_sync_progress(session, media_type, pages[-1], total_pages_discovered)

                await self._increment_stat(f"{stat_key}_processed", len(results))
                failed = len(pages) * 20 - len(results)  # Approximate failed count
                if failed > 0:
                    await self._increment_stat(f"{stat_key}_failed", failed)

            # Progress log
            logger.info(f"{media_type.title()} progress: {self.stats[f'{stat_key}_processed']} processed, "
                       f"{self.stats[f'{stat_key}_failed']} failed")

            current_page = batch_end

        # Mark as completed
        async with get_session() as session:
            await update_sync_progress(session, media_type, self.max_pages, self.max_pages, "completed")

        logger.info(f"{media_type.title()} import complete. "
                   f"Processed: {self.stats[f'{stat_key}_processed']}, "
                   f"Failed: {self.stats[f'{stat_key}_failed']}")

    async def run(self, import_movies: bool = True, import_tv: bool = True):
        """Run the import process."""
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("TMDB High-Performance Import Started")
        logger.info(f"Mode: {'Light' if self.light_mode else 'Full'}")
        logger.info(f"Max pages: {self.max_pages}")
        logger.info(f"Parallel workers: {self.max_workers}")
        logger.info(f"Pages per batch: {self.pages_per_batch}")
        logger.info(f"Import movies: {import_movies}, Import TV: {import_tv}")
        logger.info("=" * 60)

        await init_db()

        async with self.client:
            # Import reference data in parallel
            await asyncio.gather(
                self.import_genres(),
                self.import_watch_providers()
            )

            if import_movies:
                await self.import_media("movie")

            if import_tv:
                await self.import_media("tv")

        await close_db()

        duration = datetime.now() - start_time
        total_processed = self.stats['movies_processed'] + self.stats['tv_processed']
        rate = total_processed / duration.total_seconds() if duration.total_seconds() > 0 else 0

        logger.info("=" * 60)
        logger.info("TMDB Import Complete")
        logger.info(f"Duration: {duration}")
        logger.info(f"Rate: {rate:.1f} items/second")
        logger.info(f"Movies: {self.stats['movies_processed']} processed, {self.stats['movies_failed']} failed")
        logger.info(f"TV Shows: {self.stats['tv_processed']} processed, {self.stats['tv_failed']} failed")
        logger.info("=" * 60)


def parse_args():
    parser = argparse.ArgumentParser(description="High-performance TMDB data importer")
    parser.add_argument("--movies", action="store_true", help="Import only movies")
    parser.add_argument("--tv", action="store_true", help="Import only TV shows")
    parser.add_argument("--light", action="store_true", help="Light mode (basic data + external IDs only)")
    parser.add_argument("--pages", type=int, default=500, help="Maximum pages to fetch (default: 500)")
    parser.add_argument("--workers", type=int, default=20, help="Parallel workers (default: 20)")
    parser.add_argument("--batch", type=int, default=5, help="Pages per batch (default: 5)")
    parser.add_argument("--reset", action="store_true", help="Reset progress and start from page 1")
    return parser.parse_args()


async def main():
    args = parse_args()

    import_movies = not args.tv or args.movies
    import_tv = not args.movies or args.tv

    if args.movies and not args.tv:
        import_tv = False
    elif args.tv and not args.movies:
        import_movies = False

    if args.reset:
        await init_db()
        async with get_session() as session:
            from sqlalchemy import delete
            from models import SyncProgress
            await session.execute(delete(SyncProgress))
            await session.commit()
        await close_db()
        logger.info("Progress reset.")

    importer = TMDBImporter(
        light_mode=args.light,
        max_pages=args.pages,
        max_workers=args.workers,
        pages_per_batch=args.batch
    )
    await importer.run(import_movies=import_movies, import_tv=import_tv)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def run_with_cleanup():
        try:
            await main()
        except KeyboardInterrupt:
            logger.info("Import cancelled by user.")
        except Exception as e:
            logger.error(f"Import failed: {e}")
        finally:
            # Ensure database is closed
            try:
                await close_db()
            except Exception:
                pass

    try:
        asyncio.run(run_with_cleanup())
    except KeyboardInterrupt:
        print("\nAborted.")
