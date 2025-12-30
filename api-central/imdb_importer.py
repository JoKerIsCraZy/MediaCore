import asyncio
import gzip
import os
import sqlite3
import logging
import aiohttp
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Request huge timeout for large files
TIMEOUT = aiohttp.ClientTimeout(total=None, connect=60, sock_read=60)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("imdb_importer")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "media_database.db"
DATA_DIR = BASE_DIR / "imdb_data"

DATASETS = {
    "title.basics": "https://datasets.imdbws.com/title.basics.tsv.gz",
    "title.ratings": "https://datasets.imdbws.com/title.ratings.tsv.gz",
    "title.akas": "https://datasets.imdbws.com/title.akas.tsv.gz",
    "title.principals": "https://datasets.imdbws.com/title.principals.tsv.gz",
    # "title.crew": "https://datasets.imdbws.com/title.crew.tsv.gz" # Principals often covers what we need for "cast" lists
}

# Filters to reduce DB size - only keep these types
# Set to True to include ~8 million episodes (warning: significantly larger DB + slower import)
INCLUDE_EPISODES = False

VALID_TYPES = {"movie", "tvSeries", "tvMiniSeries", "tvMovie"}
if INCLUDE_EPISODES:
    VALID_TYPES.add("tvEpisode")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -100000;") # 100MB cache
    return conn

async def download_file(session, url, dest_path):
    if dest_path.exists():
        logger.info(f"File {dest_path.name} already exists. Skipping download.")
        return dest_path

    logger.info(f"Downloading {url}...")
    try:
        async with session.get(url, timeout=TIMEOUT) as response:
            if response.status != 200:
                logger.error(f"Failed to download {url}: {response.status}")
                return None
            
            with open(dest_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(1024 * 1024): # 1MB chunks
                    f.write(chunk)
        logger.info(f"Downloaded {dest_path.name}")
        return dest_path
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return None

def process_basics(file_path):
    logger.info("Processing title.basics...")
    conn = get_db_connection()
    c = conn.cursor()
    
    # Drop and recreate for full refresh (fastest)
    c.execute("DROP TABLE IF EXISTS imdb_titles")
    c.execute("""
        CREATE TABLE imdb_titles (
            tconst TEXT PRIMARY KEY,
            titleType TEXT,
            primaryTitle TEXT,
            originalTitle TEXT,
            isAdult BOOLEAN,
            startYear INTEGER,
            endYear INTEGER,
            runtimeMinutes INTEGER,
            genres TEXT
        )
    """)
    conn.commit()

    batch = []
    count = 0
    kept_tconsts = set()

    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        next(f) # Skip header
        for line in f:
            parts = line.strip().split('\t')
            # tconst, titleType, primaryTitle, originalTitle, isAdult, startYear, endYear, runtimeMinutes, genres
            if len(parts) < 9: continue
            
            tconst, tType = parts[0], parts[1]
            
            if tType in VALID_TYPES:
                # Convert \N to None
                row = [None if p == '\\N' else p for p in parts[:9]]
                batch.append(row)
                kept_tconsts.add(tconst)
                count += 1
            
            if len(batch) >= 50000:
                c.executemany("INSERT INTO imdb_titles VALUES (?,?,?,?,?,?,?,?,?)", batch)
                conn.commit()
                batch = []
                print(f"Imported {count} titles...", end='\r')

    if batch:
        c.executemany("INSERT INTO imdb_titles VALUES (?,?,?,?,?,?,?,?,?)", batch)
        conn.commit()

    logger.info(f"Finished title.basics. Imported {count} titles.")
    
    # Create indexes
    logger.info("Creating indexes for basics...")
    c.execute("CREATE INDEX IF NOT EXISTS idx_imdb_titles_type ON imdb_titles(titleType)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_imdb_titles_primary ON imdb_titles(primaryTitle)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_imdb_titles_year ON imdb_titles(startYear)")
    conn.commit()
    conn.close()
    return kept_tconsts

def process_ratings(file_path, valid_tconsts):
    logger.info("Processing title.ratings...")
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("DROP TABLE IF EXISTS imdb_ratings")
    c.execute("""
        CREATE TABLE imdb_ratings (
            tconst TEXT PRIMARY KEY,
            averageRating REAL,
            numVotes INTEGER
        )
    """)
    conn.commit()

    batch = []
    count = 0
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        next(f)
        for line in f:
            parts = line.strip().split('\t')
            tconst = parts[0]
            
            if tconst in valid_tconsts:
                # tconst, averageRating, numVotes
                batch.append((parts[0], parts[1], parts[2]))
                count += 1
            
            if len(batch) >= 50000:
                c.executemany("INSERT INTO imdb_ratings VALUES (?,?,?)", batch)
                conn.commit()
                batch = []
                print(f"Imported {count} ratings...", end='\r')

    if batch:
        c.executemany("INSERT INTO imdb_ratings VALUES (?,?,?)", batch)
        conn.commit()

    logger.info(f"Finished title.ratings. Imported {count} ratings.")
    c.execute("CREATE INDEX IF NOT EXISTS idx_imdb_ratings_rating ON imdb_ratings(averageRating)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_imdb_ratings_votes ON imdb_ratings(numVotes)")
    conn.commit()
    conn.close()

def process_akas(file_path, valid_tconsts):
    logger.info("Processing title.akas...")
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("DROP TABLE IF EXISTS imdb_akas")
    c.execute("""
        CREATE TABLE imdb_akas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titleId TEXT,
            ordering INTEGER,
            title TEXT,
            region TEXT,
            language TEXT,
            types TEXT,
            attributes TEXT,
            isOriginalTitle BOOLEAN
        )
    """)
    conn.commit()

    batch = []
    count = 0
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        next(f)
        for line in f:
            parts = line.strip().split('\t')
            titleId = parts[0]
            
            if titleId in valid_tconsts:
                # titleId, ordering, title, region, language, types, attributes, isOriginalTitle
                # Note: TSV has 8 cols usually
                # Convert \N to None
                row = [None if p == '\\N' else p for p in parts[:8]]
                
                # Insert excluding ID which is auto
                batch.append(row)
                count += 1
            
            if len(batch) >= 50000:
                c.executemany("INSERT INTO imdb_akas (titleId, ordering, title, region, language, types, attributes, isOriginalTitle) VALUES (?,?,?,?,?,?,?,?)", batch)
                conn.commit()
                batch = []
                print(f"Imported {count} akas...", end='\r')

    if batch:
        c.executemany("INSERT INTO imdb_akas (titleId, ordering, title, region, language, types, attributes, isOriginalTitle) VALUES (?,?,?,?,?,?,?,?)", batch)
        conn.commit()

    logger.info(f"Finished title.akas. Imported {count} entries.")
    c.execute("CREATE INDEX IF NOT EXISTS idx_imdb_akas_titleId ON imdb_akas(titleId)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_imdb_akas_title ON imdb_akas(title)")
    conn.commit()
    conn.close()

def process_principals(file_path, valid_tconsts):
    logger.info("Processing title.principals...")
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("DROP TABLE IF EXISTS imdb_principals")
    c.execute("""
        CREATE TABLE imdb_principals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tconst TEXT,
            ordering INTEGER,
            nconst TEXT,
            category TEXT,
            job TEXT,
            characters TEXT
        )
    """)
    conn.commit()

    batch = []
    count = 0
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        next(f)
        for line in f:
            parts = line.strip().split('\t')
            tconst = parts[0]
            
            if tconst in valid_tconsts:
                # tconst, ordering, nconst, category, job, characters
                row = [None if p == '\\N' else p for p in parts[:6]]
                batch.append(row)
                count += 1
            
            if len(batch) >= 50000:
                c.executemany("INSERT INTO imdb_principals (tconst, ordering, nconst, category, job, characters) VALUES (?,?,?,?,?,?)", batch)
                conn.commit()
                batch = []
                print(f"Imported {count} principals...", end='\r')

    if batch:
        c.executemany("INSERT INTO imdb_principals (tconst, ordering, nconst, category, job, characters) VALUES (?,?,?,?,?,?)", batch)
        conn.commit()

    logger.info(f"Finished title.principals. Imported {count} entries.")
    c.execute("CREATE INDEX IF NOT EXISTS idx_imdb_principals_tconst ON imdb_principals(tconst)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_imdb_principals_nconst ON imdb_principals(nconst)")
    conn.commit()
    conn.close()

async def pipeline():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. Download all concurrently
    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, url in DATASETS.items():
            dest = DATA_DIR / f"{name}.tsv.gz"
            tasks.append(download_file(session, url, dest))
        
        downloaded = await asyncio.gather(*tasks)
    
    files = {name: path for name, path in zip(DATASETS.keys(), downloaded) if path}
    
    if "title.basics" not in files:
        logger.error("Missing title.basics! Cannot proceed.")
        return

    # 2. Process basics first to get the valid tconst set (Filter for movies/Series)
    # Using ThreadPool to keep UI/Loop responsive if needed, though this is a script.
    
    loop = asyncio.get_running_loop()
    
    # We must run basics first to populate VALID_TCONSTS
    valid_tconsts = await loop.run_in_executor(None, process_basics, files["title.basics"])
    logger.info(f"Found {len(valid_tconsts)} valid movies/series.")

    # 3. Process others in sequence (SQLite write lock prevents parallel writes effectively anyway)
    # We could parallelize if we had multiple DB connections and WAL mode fully tuned, 
    # but sequential is safer for avoiding "database is locked".
    
    if "title.ratings" in files:
        await loop.run_in_executor(None, process_ratings, files["title.ratings"], valid_tconsts)
    
    if "title.akas" in files:
        await loop.run_in_executor(None, process_akas, files["title.akas"], valid_tconsts) # Requires filtered check potentially? Yes, added arg.
        
    if "title.principals" in files:
        await loop.run_in_executor(None, process_principals, files["title.principals"], valid_tconsts)
        
    logger.info("First clean up...")
    # Optional: Delete gz files to save space? User has space? 
    # Let's keep them for now, user can delete.
    
    logger.info("IMDb Import Complete!")

if __name__ == "__main__":
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(pipeline())
