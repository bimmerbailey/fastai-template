from pathlib import Path

import anyio
from alembic import command
from alembic.config import Config
from anyio import to_thread
from faker import Faker
from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.auth import RefreshToken, UserOAuthAccount
from fastai.chats.models import Conversation, Message
from fastai.database.core import create_db_engine, destroy_engine
from fastai.documents.models import Document
from fastai.embeddings.models import Embedding
from fastai.storage.core import StorageSettings
from fastai.users.models import User
from fastai.users.schemas import UserCreate

fake = Faker()

# ── Static users ──

STATIC_USERS: list[dict[str, str | bool]] = [
    {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "password": "password1234",
        "is_admin": True,
    },
    {
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Johnson",
        "password": "password1234",
        "is_admin": False,
    },
    {
        "email": "bob@example.com",
        "first_name": "Bob",
        "last_name": "Smith",
        "password": "password1234",
        "is_admin": False,
    },
    {
        "email": "carol@example.com",
        "first_name": "Carol",
        "last_name": "Williams",
        "password": "password1234",
        "is_admin": False,
    },
    {
        "email": "dave@example.com",
        "first_name": "Dave",
        "last_name": "Brown",
        "password": "password1234",
        "is_admin": False,
    },
]


async def create_users(session: AsyncSession) -> list[User]:
    """Create static users and a batch of random users."""
    users: list[User] = []

    # Static users
    for data in STATIC_USERS:
        to_create = UserCreate.model_validate(data)
        user = await User.create(session, to_create)  # type: ignore[arg-type]
        users.append(user)
        print(f"  Created user: {user.email} (admin={user.is_admin})")

    # Random users
    for _ in range(10):
        user = await User.create(
            session,
            UserCreate(
                email=fake.unique.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password="password1234",
            ),
        )
        users.append(user)
        print(f"  Created user: {user.email}")

    return users


async def ensure_bucket() -> None:
    """Create the S3 storage bucket if it doesn't already exist."""
    settings = StorageSettings()  # pyright: ignore[reportCallIssue]
    async with settings.create_resource() as resource:
        bucket = await resource.Bucket(settings.bucket)
        try:
            await bucket.meta.client.head_bucket(Bucket=settings.bucket)
            print(f"Bucket '{settings.bucket}' already exists.")
        except Exception:
            await resource.create_bucket(Bucket=settings.bucket)
            print(f"Created bucket '{settings.bucket}'.")


def run_migrations() -> None:
    """Run alembic migrations (upgrade head)."""
    root = Path(__file__).resolve().parent.parent
    alembic_cfg = Config(str(root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied successfully.")


async def seed_database(session: AsyncSession) -> None:
    """Run the full database seed."""
    await to_thread.run_sync(run_migrations)

    print("Ensuring storage bucket exists...")
    await ensure_bucket()

    print("Creating users...")
    await create_users(session)

    print("\nDone! Database seeded successfully.")


async def drop_tables(session: AsyncSession) -> None:
    for table in [
        Embedding,
        Message,
        Conversation,
        RefreshToken,
        UserOAuthAccount,
        User,
        Document,
    ]:
        await session.exec(delete(table))
        await session.commit()


async def _main() -> None:
    engine = create_db_engine()
    async with AsyncSession(engine) as session:
        try:
            await drop_tables(session)
        except Exception:
            await session.rollback()
        await seed_database(session)
    await destroy_engine(engine)


def main() -> None:
    """Sync entry point for the ``seed`` console script."""
    anyio.run(_main)


if __name__ == "__main__":
    main()
