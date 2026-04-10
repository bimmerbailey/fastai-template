import uuid

import structlog.stdlib
from fastapi import APIRouter, HTTPException, Query, status

from fastai.api_v1.dependencies import (
    CurrentAdminDep,
    CurrentUserDep,
    KnowledgeBaseDep,
)
from fastai.embeddings.core import KnowledgeBase, build_item_text
from fastai.embeddings.exceptions import EmbeddingError
from fastai.embeddings.models import Embedding
from fastai.items.models import Item
from fastai.items.schemas import ItemCreate, ItemRead, ItemUpdate
from fastai.utils.dependencies import SessionDep

logger = structlog.stdlib.get_logger(__name__)

router = APIRouter(prefix="/items", tags=["Items"])


# TODO: Remove once we add documents
async def _embed_item(session: SessionDep, item: Item, kb: KnowledgeBase) -> None:
    """Build text from item fields and store the embedding. Logs and swallows errors."""
    try:
        content = build_item_text(
            name=item.name,
            description=item.description,
            cost=item.cost,
            quantity=item.quantity,
        )
        await kb.embed_and_store(
            session,
            source_type="item",
            source_id=item.id,
            content=content,
            metadata={"name": item.name},
        )
        await session.refresh(item)
    except EmbeddingError:
        logger.warning(
            "Failed to embed item, continuing without embedding",
            item_id=str(item.id),
            exc_info=True,
        )


@router.get("", response_model=list[ItemRead])
async def list_items(
    session: SessionDep,
    _: CurrentUserDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[Item]:
    """List all items with pagination."""
    return await Item.get_all(session, offset=offset, limit=limit)


@router.get("/{item_id}", response_model=ItemRead)
async def get_item(session: SessionDep, _: CurrentUserDep, item_id: uuid.UUID) -> Item:
    """Get a single item by ID."""
    item = await Item.get(session, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return item


# TODO: Move to admin api
@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    session: SessionDep,
    _: CurrentAdminDep,
    item_in: ItemCreate,
    kb: KnowledgeBaseDep,
) -> Item:
    """Create a new item."""
    item = await Item.create(session, item_in)
    await _embed_item(session, item, kb)
    return item


@router.patch("/{item_id}", response_model=ItemRead)
async def update_item(
    session: SessionDep,
    _: CurrentUserDep,
    item_id: uuid.UUID,
    item_in: ItemUpdate,
    kb: KnowledgeBaseDep,
) -> Item:
    """Partially update an item."""
    item = await Item.get(session, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    item = await item.update(session, item_in)
    await _embed_item(session, item, kb)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    session: SessionDep,
    _: CurrentAdminDep,
    item_id: uuid.UUID,
) -> None:
    """Delete an item."""
    item = await Item.get(session, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    await Embedding.delete_by_source(session, "item", item.id)
    await item.delete(session)
