from __future__ import annotations

from sqlmodel import Column, Field, Integer, String, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.users.schemas import UserBase, UserCreate, UserUpdate
from fastai.utils.models import TimestampMixin


class User(UserBase, TimestampMixin, table=True):
    """Database table model for users."""

    __tablename__ = "users"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    password: str = Field(sa_column=Column(String, nullable=False))
    is_admin: bool = Field(default=False)

    @classmethod
    async def create(cls, session: AsyncSession, user_in: UserCreate) -> User:
        """Create a new user and persist it to the database."""
        user = cls.model_validate(user_in)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def get(cls, session: AsyncSession, user_id: int) -> User | None:
        """Get a single user by ID. Returns None if not found."""
        return await session.get(cls, user_id)

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> User | None:
        """Get a single user by email. Returns None if not found."""
        statement = select(cls).where(cls.email == email)
        results = await session.exec(statement)
        return results.first()

    @classmethod
    async def get_all(
        cls, session: AsyncSession, offset: int = 0, limit: int = 100
    ) -> list[User]:
        """Get a paginated list of users."""
        statement = select(cls).offset(offset).limit(limit)
        results = await session.exec(statement)
        return list(results.all())

    async def update(self, session: AsyncSession, user_in: UserUpdate) -> User:
        """Update this user with partial data."""
        update_data = user_in.model_dump(exclude_unset=True)
        self.sqlmodel_update(update_data)
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete this user from the database."""
        await session.delete(self)
        await session.commit()
