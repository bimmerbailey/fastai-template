from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from fastai.users.models import User
from fastai.users.schemas import UserCreate, UserRead, UserUpdate
from fastai.utils.dependencies import SessionDep

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserRead])
async def list_users(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[User]:
    """List all users with pagination."""
    return await User.get_all(session, offset=offset, limit=limit)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(session: SessionDep, user_id: uuid.UUID) -> User:
    """Get a single user by ID."""
    user = await User.get(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(session: SessionDep, user_in: UserCreate) -> User:
    """Create a new user."""
    existing = await User.get_by_email(session, user_in.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    return await User.create(session, user_in)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> User:
    """Partially update a user."""
    user = await User.get(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # If email is being changed, check for conflicts
    if user_in.email is not None and user_in.email != user.email:
        existing = await User.get_by_email(session, user_in.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

    return await user.update(session, user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(session: SessionDep, user_id: uuid.UUID) -> None:
    """Soft-delete a user."""
    user = await User.get(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    await user.soft_delete(session)
