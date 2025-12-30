import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine

# Add current dir to path
sys.path.append(os.getcwd())

from config import Settings
settings = Settings()
from models_media import Base

async def init_tables():
    print(f"Connecting to: {settings.database_url}")
    engine = create_async_engine(settings.database_url)
    
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_tables())
