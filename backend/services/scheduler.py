from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def update_list(list_id: int, session: AsyncSession):
    """
    Update a single list by re-running its filters.
    """
    from models import List, ListItem
    from services.filter_engine import filter_engine
    
    try:
        # Get the list
        result = await session.execute(
            select(List).where(List.id == list_id)
        )
        media_list = result.scalar_one_or_none()
        
        if not media_list:
            logger.warning(f"List {list_id} not found for update")
            return
        
        logger.info(f"Updating list: {media_list.name}")
        
        # Get new results from filter engine
        results = await filter_engine.get_all_results(
            media_type=media_list.media_type.value,
            filters=media_list.filters or [],
            filter_operator=media_list.filter_operator.value,
            sort_by=media_list.sort_by,
            limit=media_list.limit,
        )
        
        # Clear existing items
        await session.execute(
            ListItem.__table__.delete().where(ListItem.list_id == list_id)
        )
        
        # Add new items
        for i, item in enumerate(results):
            list_item = ListItem(
                list_id=list_id,
                tmdb_id=item["tmdb_id"],
                imdb_id=item.get("imdb_id"),
                tvdb_id=item.get("tvdb_id"),
                media_type=media_list.media_type,
                title=item.get("title"),
                original_title=item.get("original_title"),
                poster_path=item.get("poster_path"),
                backdrop_path=item.get("backdrop_path"),
                overview=item.get("overview"),
                release_date=item.get("release_date"),
                vote_average=item.get("vote_average"),
                vote_count=item.get("vote_count"),
                popularity=item.get("popularity"),
                position=i,
            )
            session.add(list_item)
        
        # Update last_updated timestamp
        media_list.last_updated = datetime.utcnow()
        
        await session.commit()
        logger.info(f"Updated list {media_list.name} with {len(results)} items")
        
    except Exception as e:
        logger.error(f"Error updating list {list_id}: {e}")
        await session.rollback()
        raise


async def update_all_lists():
    """
    Update all lists that need updating based on their interval.
    """
    from database import async_session
    from models import List
    
    async with async_session() as session:
        try:
            # Find lists that need updating
            now = datetime.utcnow()
            result = await session.execute(
                select(List).where(List.auto_update == True)
            )
            lists = result.scalars().all()
            
            for media_list in lists:
                # Check if update is needed
                if media_list.last_updated:
                    next_update = media_list.last_updated + timedelta(
                        hours=media_list.update_interval
                    )
                    if now < next_update:
                        continue
                
                # Update this list
                await update_list(media_list.id, session)
            
            logger.info(f"Completed update check for {len(lists)} lists")
            
        except Exception as e:
            logger.error(f"Error in update_all_lists: {e}")


def start_scheduler():
    """Start the background scheduler."""
    from config import get_settings
    settings = get_settings()
    
    # Add job to check for list updates every hour
    scheduler.add_job(
        update_all_lists,
        IntervalTrigger(hours=1),
        id="update_lists",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
