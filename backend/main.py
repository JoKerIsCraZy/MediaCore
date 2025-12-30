from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from config import get_settings
from database import init_db, close_db
from routers import lists, media
from services.tmdb import tmdb_service
from services.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Path to frontend static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting JokerList...")
    await init_db()
    start_scheduler()
    logger.info("JokerList started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down JokerList...")
    stop_scheduler()
    await tmdb_service.close()
    await close_db()
    logger.info("JokerList shut down successfully!")


# Create FastAPI app
app = FastAPI(
    title="MediaCore",
    description="Central Media Data Hub",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(lists.router, prefix="/api")
app.include_router(media.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}


# Serve static frontend files if the directory exists
if os.path.isdir(STATIC_DIR):
    # Mount static files for assets
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the SPA for all non-API routes."""
        # Check if file exists in static dir
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Return index.html for SPA routing
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/")
    async def root():
        """Root endpoint when no frontend is built."""
        return {
            "name": "JokerList",
            "version": "1.0.0",
            "docs": "/docs",
            "message": "Frontend not built. Visit /docs for API documentation."
        }


if __name__ == "__main__":
    import uvicorn
    import sys

    # Fix asyncio event loop policy for Windows
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
