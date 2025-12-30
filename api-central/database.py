from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from models import Base, SyncProgress
from config import DATABASE_URL


engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_session() -> AsyncSession:
    """Get a database session."""
    async with async_session() as session:
        yield session


async def get_sync_progress(session: AsyncSession, media_type: str) -> SyncProgress:
    """Get or create sync progress for a media type."""
    result = await session.execute(
        select(SyncProgress).where(SyncProgress.media_type == media_type)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        progress = SyncProgress(media_type=media_type, last_page=0)
        session.add(progress)
        await session.commit()

    return progress


async def update_sync_progress(
    session: AsyncSession,
    media_type: str,
    last_page: int,
    total_pages: int = None,
    status: str = "in_progress"
):
    """Update sync progress."""
    result = await session.execute(
        select(SyncProgress).where(SyncProgress.media_type == media_type)
    )
    progress = result.scalar_one_or_none()

    if progress:
        progress.last_page = last_page
        if total_pages:
            progress.total_pages = total_pages
        progress.status = status
        await session.commit()

async def close_db():
    """Close access to the database."""
    await engine.dispose()
