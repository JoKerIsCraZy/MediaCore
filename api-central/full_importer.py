import asyncio
import logging
import os
import sys
from pathlib import Path

# Add current dir to path to find modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, close_db, get_session, update_sync_progress, get_sync_progress
from models import Movie
from tmdb_client import tmdb_client
from imdb_importer import pipeline as imdb_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("full_import.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("full_importer")

BATCH_SIZE = 100
MAX_WORKERS = 10

async def process_tmdb_movie_light(queue, session_factory):
    """
    Worker for Light Mode: Only fetches external IDs.
    We assume the basic data (from discover) provides the rating and title.
    We just need linking IDs.
    """
    async with session_factory() as session:
        while True:
            try:
                movie_basic = await queue.get()
                movie_id = movie_basic["id"]
                
                try:
                    # 1. Fetch External IDs (to link with IMDb)
                    # We utilize the client but focused on light data
                    # Check if we already have it to skip API call? 
                    # For an "updater", we might want to refresh ratings though.
                    # But ratings come from 'discover' result 'movie_basic', so we have fresh ratings!
                    # We mainly need external_ids if missing.
                    
                    # Optimization: If we trust Discover for ratings, we only need API call for IMDB ID.
                    # AND we can skip this call if we already have an IMDB ID in DB?
                    # But user wants "update", maybe IMDb ID changed? Unlikely.
                    # Let's blindly fetch to be safe and simple, or check DB. mechanism.
                    
                    # For now: 1 API call to get external_ids
                    # We use get_movie_external_ids directly
                    ids = await tmdb_client.get_movie_external_ids(movie_id)
                    imdb_id = ids.get("imdb_id") if ids else None
                    
                    # 2. Update/Insert DB
                    # We construct a Movie object with ONLY the fields we care about + basics
                    # This implies other fields (overview, etc) might be overwritten with None if we use merge with a partial object?
                    # SQLAlchemy merge: If we pass an object, it replaces.
                    # If we want to strictly update specific cols, we should use UPDATE statement.
                    # But here we are "Light Mode", maybe we claim this IS the source of truth.
                    
                    movie_data = {
                        "id": movie_id,
                        "title": movie_basic.get("title"),
                        "imdb_id": imdb_id,
                        "vote_average": movie_basic.get("vote_average"),
                        "vote_count": movie_basic.get("vote_count"),
                        "release_date": movie_basic.get("release_date"),
                        # Keep minimal
                    }
                    
                    # Use merge (creates or updates). 
                    # Note: This will set unspecified columns to Null if they didn't exist, 
                    # or keep existing if mapped correctly? 
                    # With merge, it usually replaces the entity.
                    # If we really just want to update ratings/ids, we should check existence.
                    
                    # Simple approach: merged object overwrites.
                    # Since we only want "Light", we accept potential loss of "Heavy" data (descriptions) if they existed?
                    # User asked for "Light" fetch. 
                    
                    movie = Movie(**movie_data)
                    await session.merge(movie)
                    await session.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing {movie_id}: {e}")
                    await session.rollback()
                finally:
                    queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker Error: {e}")
                queue.task_done()

async def run_tmdb_update():
    """Fetch TMDB data in Light Mode."""
    logger.info("Starting TMDB Update (Light Mode)...")
    
    async with get_session() as session:
        # We process page by page
        # How many pages? "All" or just "Updates"?
        # Discover endpoint strictly returns "ranked by popularity" if we ask.
        # So iterating pages 1..500 gives the top 10,000 movies.
        # This acts as an auto-updater for the most relevant movies.
        
        start_page = 1
        total_pages = 500 # Limit to top 10k for speed/relevance
        
        queue = asyncio.Queue(maxsize=BATCH_SIZE * 2)
        workers = [
            asyncio.create_task(process_tmdb_movie_light(queue, get_session))
            for _ in range(MAX_WORKERS)
        ]
        
        try:
            for page in range(start_page, total_pages + 1):
                logger.info(f"Scanning TMDB Page {page}/{total_pages}...")
                data = await tmdb_client.discover_movies(page=page)
                
                if data and "results" in data:
                    for m in data["results"]:
                        await queue.put(m)
                
            await queue.join()
            
        finally:
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

    logger.info("TMDB Update Complete.")

async def main():
    await init_db()
    
    # 1. IMDb Import (Full Refresh)
    # Checks for new files, downloads, and rebuilds IMDb tables
    logger.info("=== STEP 1: IMDb Import ===")
    await imdb_pipeline()
    
    # 2. TMDB Update (Light)
    # Fetches ratings and IDs for popular movies
    logger.info("=== STEP 2: TMDB Update ===")
    async with tmdb_client:
        await run_tmdb_update()
        
    await close_db()
    logger.info("Full update finished successfully.")

if __name__ == "__main__":
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
