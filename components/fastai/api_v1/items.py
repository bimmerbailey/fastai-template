from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from fastai.api_v1.dependencies import CurrentAdminDep, CurrentUserDep
from fastai.items.models import Item
from fastai.items.schemas import ItemCreate, ItemRead, ItemUpdate
from fastai.utils.dependencies import SessionDep

router = APIRouter(prefix="/items", tags=["Items"])


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


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    session: SessionDep, _: CurrentAdminDep, item_in: ItemCreate
) -> Item:
    """Create a new item."""
    return await Item.create(session, item_in)


@router.patch("/{item_id}", response_model=ItemRead)
async def update_item(
    session: SessionDep,
    _: CurrentUserDep,
    item_id: uuid.UUID,
    item_in: ItemUpdate,
) -> Item:
    """Partially update an item."""
    item = await Item.get(session, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return await item.update(session, item_in)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    session: SessionDep, _: CurrentAdminDep, item_id: uuid.UUID
) -> None:
    """Delete an item."""
    item = await Item.get(session, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    await item.delete(session)
