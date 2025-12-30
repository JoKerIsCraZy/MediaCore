import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
import json
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
from sqlalchemy import select, func
from typing import List as ListType, Optional
from datetime import datetime

from database import get_db
from models import List, ListItem, MediaType, FilterOperator
from schemas import (
    ListCreate, ListUpdate, ListResponse, ListDetailResponse,
    ListItemResponse, DiscoverRequest, DiscoverResponse,
)
from services.filter_engine import filter_engine
from services.scheduler import update_list

router = APIRouter(prefix="/lists", tags=["Lists"])


@router.get("", response_model=ListType[ListResponse])
async def get_all_lists(
    media_type: Optional[MediaType] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all lists, optionally filtered by media type."""
    query = select(List)
    if media_type:
        query = query.where(List.media_type == media_type)
    query = query.order_by(List.created_at.desc())
    
    result = await db.execute(query)
    lists = result.scalars().all()
    
    # Add item counts
    response = []
    for lst in lists:
        count_result = await db.execute(
            select(func.count(ListItem.id)).where(ListItem.list_id == lst.id)
        )
        item_count = count_result.scalar() or 0
        
        list_dict = {
            "id": lst.id,
            "name": lst.name,
            "description": lst.description,
            "media_type": lst.media_type,
            "filters": lst.filters,
            "filter_operator": lst.filter_operator,
            "sort_by": lst.sort_by,
            "limit": lst.limit,
            "auto_update": lst.auto_update,
            "update_interval": lst.update_interval,
            "last_updated": lst.last_updated,
            "created_at": lst.created_at,
            "updated_at": lst.updated_at,
            "item_count": item_count,
        }
        response.append(ListResponse(**list_dict))
    
    return response


@router.post("", response_model=ListResponse, status_code=201)
async def create_list(
    data: ListCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new list."""
    media_list = List(
        name=data.name,
        description=data.description,
        media_type=data.media_type,
        filters=data.filters,
        filter_operator=data.filter_operator,
        sort_by=data.sort_by,
        limit=data.limit,
        auto_update=data.auto_update,
        update_interval=data.update_interval,
    )
    db.add(media_list)
    await db.flush()
    
    # Populate list with initial items
    await update_list(media_list.id, db)
    
    return ListResponse(
        id=media_list.id,
        name=media_list.name,
        description=media_list.description,
        media_type=media_list.media_type,
        filters=media_list.filters,
        filter_operator=media_list.filter_operator,
        sort_by=media_list.sort_by,
        limit=media_list.limit,
        auto_update=media_list.auto_update,
        update_interval=media_list.update_interval,
        last_updated=media_list.last_updated,
        created_at=media_list.created_at,
        updated_at=media_list.updated_at,
        item_count=media_list.limit,
    )


@router.get("/{list_id}", response_model=ListDetailResponse)
async def get_list(
    list_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a list with all its items."""
    result = await db.execute(select(List).where(List.id == list_id))
    media_list = result.scalar_one_or_none()
    
    if not media_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Get items
    items_result = await db.execute(
        select(ListItem)
        .where(ListItem.list_id == list_id)
        .order_by(ListItem.position)
    )
    items = items_result.scalars().all()
    
    # Convert to dicts for enrichment
    # Using ListItemResponse.model_validate first to handle property conversion if logic exists?
    # No, model validation is strict. Better to use dict construction manually or __dict__ if simple.
    # ListItem is ORM.
    
    from services.local_discover import local_discover_service
    
    items_data = []
    for item in items:
        # Basic dict conversion
        d = {
            "id": item.id,
            "tmdb_id": item.tmdb_id, # Ensure tmdb_id is present for enrichment
            "imdb_id": item.imdb_id,
            "media_type": item.media_type,
            "title": item.title,
            "original_title": item.original_title,
            "poster_path": item.poster_path,
            "backdrop_path": item.backdrop_path,
            "overview": item.overview,
            "release_date": item.release_date,
            "vote_average": item.vote_average,
            "vote_count": item.vote_count,
            "popularity": item.popularity,
            "position": item.position,
            "added_at": item.added_at,
        }
        items_data.append(d)
        
    # Enrich
    if items_data:
        try:
            items_data = await local_discover_service.enrich_movies_with_ratings(items_data)
        except Exception as e:
            logger.error(f"Failed to enrich list items: {e}")
            
    # Convert to Response Model
    # Since items_data now contains imdb_rating/votes, and we updated schema, it should pass.
    
    return ListDetailResponse(
        id=media_list.id,
        name=media_list.name,
        description=media_list.description,
        media_type=media_list.media_type,
        filters=media_list.filters,
        filter_operator=media_list.filter_operator,
        sort_by=media_list.sort_by,
        limit=media_list.limit,
        auto_update=media_list.auto_update,
        update_interval=media_list.update_interval,
        last_updated=media_list.last_updated,
        created_at=media_list.created_at,
        updated_at=media_list.updated_at,
        item_count=len(items),
        items=[ListItemResponse(**item) for item in items_data],
    )


@router.patch("/{list_id}", response_model=ListResponse)
async def update_list_endpoint(
    list_id: int,
    data: ListUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a list's settings."""
    result = await db.execute(select(List).where(List.id == list_id))
    media_list = result.scalar_one_or_none()
    
    if not media_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Track if filters changed
    filters_changed = False
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ["filters", "filter_operator", "sort_by", "limit"]:
            filters_changed = True
        setattr(media_list, field, value)
    
    media_list.updated_at = datetime.utcnow()
    await db.flush()
    
    # Re-populate if filters changed
    if filters_changed:
        await update_list(list_id, db)
    
    # Get item count
    count_result = await db.execute(
        select(func.count(ListItem.id)).where(ListItem.list_id == list_id)
    )
    item_count = count_result.scalar() or 0
    
    return ListResponse(
        id=media_list.id,
        name=media_list.name,
        description=media_list.description,
        media_type=media_list.media_type,
        filters=media_list.filters,
        filter_operator=media_list.filter_operator,
        sort_by=media_list.sort_by,
        limit=media_list.limit,
        auto_update=media_list.auto_update,
        update_interval=media_list.update_interval,
        last_updated=media_list.last_updated,
        created_at=media_list.created_at,
        updated_at=media_list.updated_at,
        item_count=item_count,
    )


@router.delete("/{list_id}", status_code=204)
async def delete_list(
    list_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a list."""
    result = await db.execute(select(List).where(List.id == list_id))
    media_list = result.scalar_one_or_none()
    
    if not media_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    await db.delete(media_list)
    return Response(status_code=204)


@router.post("/{list_id}/refresh", response_model=ListResponse)
async def refresh_list(
    list_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Manually refresh a list."""
    result = await db.execute(select(List).where(List.id == list_id))
    media_list = result.scalar_one_or_none()
    
    if not media_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    await update_list(list_id, db)
    
    # Get updated item count
    count_result = await db.execute(
        select(func.count(ListItem.id)).where(ListItem.list_id == list_id)
    )
    item_count = count_result.scalar() or 0
    
    # Refresh the list object
    await db.refresh(media_list)
    
    return ListResponse(
        id=media_list.id,
        name=media_list.name,
        description=media_list.description,
        media_type=media_list.media_type,
        filters=media_list.filters,
        filter_operator=media_list.filter_operator,
        sort_by=media_list.sort_by,
        limit=media_list.limit,
        auto_update=media_list.auto_update,
        update_interval=media_list.update_interval,
        last_updated=media_list.last_updated,
        created_at=media_list.created_at,
        updated_at=media_list.updated_at,
        item_count=item_count,
    )


# ============ Export Endpoints ============

@router.get("/{list_id}/export/json")
async def export_list_json(
    list_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export list as JSON."""
    result = await db.execute(select(List).where(List.id == list_id))
    media_list = result.scalar_one_or_none()
    
    if not media_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    items_result = await db.execute(
        select(ListItem)
        .where(ListItem.list_id == list_id)
        .order_by(ListItem.position)
    )
    items = items_result.scalars().all()
    
    data = {
        "name": media_list.name,
        "media_type": media_list.media_type.value,
        "items": [
            {
                "tmdb_id": item.tmdb_id,
                "imdb_id": item.imdb_id,
                "title": item.title,
                "year": item.release_date[:4] if item.release_date else None,
            }
            for item in items
        ]
    }
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json"
    )


@router.get("/{list_id}/export/radarr")
async def export_list_radarr(
    list_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export list in Radarr-compatible format (uses cached IMDB IDs)."""
    result = await db.execute(select(List).where(List.id == list_id))
    media_list = result.scalar_one_or_none()

    if not media_list:
        raise HTTPException(status_code=404, detail="List not found")

    if media_list.media_type != MediaType.MOVIE:
        raise HTTPException(
            status_code=400,
            detail="Radarr export only available for movie lists"
        )

    items_result = await db.execute(
        select(ListItem)
        .where(ListItem.list_id == list_id)
        .order_by(ListItem.position)
    )
    items = items_result.scalars().all()

    # Radarr format: [{"id": tmdb_id}, ...]
    results = [{"id": item.tmdb_id} for item in items]

    return Response(
        content=json.dumps(results),
        media_type="application/json"
    )


@router.get("/{list_id}/export/sonarr")
async def export_list_sonarr(
    list_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export list in Sonarr-compatible format (uses cached TVDB IDs)."""
    result = await db.execute(select(List).where(List.id == list_id))
    media_list = result.scalar_one_or_none()

    if not media_list:
        raise HTTPException(status_code=404, detail="List not found")

    if media_list.media_type != MediaType.TV:
        raise HTTPException(
            status_code=400,
            detail="Sonarr export only available for TV lists"
        )

    items_result = await db.execute(
        select(ListItem)
        .where(ListItem.list_id == list_id)
        .order_by(ListItem.position)
    )
    items = items_result.scalars().all()

    # Sonarr format: [{"tvdbId": "value"}, ...]
    results = [{"tvdbId": str(item.tvdb_id)} for item in items if item.tvdb_id]

    return Response(
        content=json.dumps(results),
        media_type="application/json"
    )


# ============ Preview Endpoint ============

@router.post("/preview", response_model=DiscoverResponse)
async def preview_filters(
    request: DiscoverRequest,
):
    """Preview results for a filter configuration without saving."""
    result = await filter_engine.discover(
        media_type=request.media_type.value,
        filters=request.filters,
        filter_operator=request.filter_operator.value,
        sort_by=request.sort_by,
        page=request.page,
    )
    
    return DiscoverResponse(**result)
