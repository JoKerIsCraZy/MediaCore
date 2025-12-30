import asyncio
import os
import sys
from sqlalchemy import select, func, text

# Add current dir to path to import models
sys.path.append(os.getcwd())

from config import Settings
settings = Settings()
from models_media import Movie, ImdbRating
from database import async_session, engine

async def check_db():
    print(f"Current working directory: {os.getcwd()}")
    print(f"Configured Database URL: {settings.database_url}")
    
    # Path validity check
    if "sqlite" in settings.database_url:
        path_part = settings.database_url.split(":///")[-1]
        abs_path = os.path.abspath(path_part)
        print(f"Checking absolute path: {abs_path}")
        if os.path.exists(abs_path):
            print(f"✅ DB file found ({os.path.getsize(abs_path)} bytes)")
        else:
            print(f"❌ DB file NOT found at {abs_path}")
            print(f"Listing ../api-central: {os.listdir('../api-central') if os.path.exists('../api-central') else 'not found'}")

    async with async_session() as session:
        print("\n--- Checking Data ---")
        try:
            # Check Movies
            stmt = select(func.count(Movie.id))
            result = await session.execute(stmt)
            movie_count = result.scalar()
            print(f"Total Movies in DB: {movie_count}")
            
            # Check Ratings
            stmt = select(func.count(ImdbRating.tconst))
            result = await session.execute(stmt)
            rating_count = result.scalar()
            print(f"Total IMDb Ratings in DB: {rating_count}")
            
            # Check for mapping issues (Movie.imdb_id vs ImdbRating.tconst)
            if movie_count > 0:
                print("\n--- Sample Movie ---")
                stmt = select(Movie).where(Movie.imdb_id.isnot(None)).limit(1)
                result = await session.execute(stmt)
                movie = result.scalar()
                if movie:
                    print(f"Movie: {movie.title}, IMDb ID: {movie.imdb_id}")
                    # Try to find its rating
                    stmt_rating = select(ImdbRating).where(ImdbRating.tconst == movie.imdb_id)
                    res_rating = await session.execute(stmt_rating)
                    rating = res_rating.scalar()
                    if rating:
                        print(f"✅ Found Rating: {rating.averageRating} ({rating.numVotes} votes)")
                    else:
                        print(f"❌ No Rating found for this IMDb ID")
                else:
                     print("No movies with IMDb IDs found.")

        except Exception as e:
            print(f"❌ Error during DB Query: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_db())
