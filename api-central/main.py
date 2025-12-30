import asyncio
import logging
import signal
from typing import List
from tqdm.asyncio import tqdm

from config import BATCH_SIZE
from database import init_db, close_db, get_session, get_sync_progress, update_sync_progress
from models import Movie
from tmdb_client import tmdb_client
from sqlalchemy.exc import IntegrityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api_central.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

# Number of concurrent workers for processing movies
# Adjusted to respect TMDB rate limit (35/10s = 3.5 req/s)
# With 10 workers, we might hit limit often, but RateLimiter handles it.
# Higher concurrency allows filling the gaps better.
NUM_WORKERS = 10 

async def process_movie_worker(queue, session_factory):
    """Worker to process movies from queue."""
    async with session_factory() as session:
        while True:
            try:
                movie_basic_data = await queue.get()
                
                movie_id = movie_basic_data["id"]
                # Process
                try:
                    # 1. Get full details (includes external_ids now)
                    details = await tmdb_client.get_movie_details(movie_id)
                    if not details:
                        queue.task_done()
                        continue

                    # 2. Parse
                    external_ids = details.get("external_ids", {})
                    movie_data = tmdb_client.parse_movie_data(movie_basic_data, details, external_ids)
                    
                    # 3. Create/Merge Model
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
                logger.error(f"Worker fatal error: {e}")
                queue.task_done()

async def fetch_movies():
    """Main loop to fetch all movies via discovery."""
    async with get_session() as session:
        progress = await get_sync_progress(session, "movie")
        start_page = progress.last_page + 1
        
    logger.info(f"Resuming from page {start_page}")

    # Initialize Queue and Workers
    queue = asyncio.Queue(maxsize=BATCH_SIZE * 2)
    workers = []
    
    # We need a session per worker or pass a factory
    # get_session is a context manager, so we pass it directly
    for _ in range(NUM_WORKERS):
        t = asyncio.create_task(process_movie_worker(queue, get_session))
        workers.append(t)

    try:
        # Initial discovery scan
        first_page_data = await tmdb_client.discover_movies(page=start_page)
        if not first_page_data:
            logger.error("Failed start.")
            return

        total_pages = min(first_page_data.get("total_pages", 500), 500)
        logger.info(f"Target pages: {total_pages - start_page + 1}")

        pbar = tqdm(total=(total_pages - start_page + 1) * 20, desc="Movies") # approx 20 per page

        for page in range(start_page, total_pages + 1):
            data = await tmdb_client.discover_movies(page=page)
            if not data or "results" not in data:
                continue

            results = data["results"]
            
            # Feed workers
            for m in results:
                await queue.put(m)
                pbar.update(1)

            # Checkpoint progress periodically
            if page % 5 == 0:
                async with get_session() as session:
                    await update_sync_progress(session, "movie", page, total_pages)
                logger.info(f"Reached page {page}")

        # Finalize
        await queue.join()
        
        # Final progress update
        async with get_session() as session:
            await update_sync_progress(session, "movie", total_pages, total_pages, "completed")
            
    except asyncio.CancelledError:
        logger.info("Main loop cancelled. Stopping workers...")
    finally:
        # Stop workers
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        logger.info("All workers stopped.")


async def main():
    await init_db()
    try:
        async with tmdb_client:
            await fetch_movies()
    finally:
        await close_db()
        logger.info("Database connection closed.")


if __name__ == "__main__":
    try:
        # Graceful shutdown handler for Windows
        # Windows doesn't fully support add_signal_handler for SIGINT in asyncio easily
        # but KeyboardInterrupt works if propagated.
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nSTOPPED BY USER (Ctrl+C). Exiting cleanly...")
        # Tasks are cancelled by asyncio.run() cleanup
    except Exception as e:
        logger.error(f"Fatal: {e}")
