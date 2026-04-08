import anyio
from decimal import Decimal
from pathlib import Path

from alembic import command
from alembic.config import Config
from faker import Faker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import delete

from fastai.database.core import create_db_engine, destroy_engine
from fastai.embeddings.core import build_item_text, embed_and_store
from fastai.embeddings.providers import create_embedder
from fastai.embeddings.settings import EmbeddingSettings
from fastai.items.models import Item
from fastai.items.schemas import ItemCreate
from fastai.users.models import User
from fastai.users.schemas import UserCreate
from fastai.chats.models import Conversation, Message
from fastai.auth import RefreshToken, UserOAuthAccount


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

# ── Sample items ──

SAMPLE_ITEMS: list[dict[str, str | int | Decimal | None]] = [
    {
        "name": "Wireless Keyboard",
        "cost": Decimal("49.99"),
        "description": "Bluetooth mechanical keyboard",
        "quantity": 25,
    },
    {
        "name": "USB-C Hub",
        "cost": Decimal("34.50"),
        "description": "7-in-1 USB-C dock with HDMI",
        "quantity": 50,
    },
    {
        "name": "Monitor Stand",
        "cost": Decimal("79.00"),
        "description": "Adjustable aluminum monitor riser",
        "quantity": 15,
    },
    {
        "name": "Webcam HD",
        "cost": Decimal("89.99"),
        "description": "1080p webcam with noise-cancelling mic",
        "quantity": 30,
    },
    {
        "name": "Desk Lamp",
        "cost": Decimal("29.99"),
        "description": "LED desk lamp with adjustable brightness",
        "quantity": 40,
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


async def create_items(session: AsyncSession) -> list[Item]:
    """Create static items and a batch of random items."""
    items: list[Item] = []

    # Static items
    for data in SAMPLE_ITEMS:
        item = await Item.create(session, ItemCreate(**data))  # type: ignore[arg-type]
        items.append(item)
        print(f"  Created item: {item.name} (${item.cost})")

    # Random items
    for _ in range(20):
        item = await Item.create(
            session,
            ItemCreate(
                name=fake.catch_phrase(),
                cost=Decimal(
                    str(
                        round(
                            fake.pyfloat(min_value=5, max_value=500, right_digits=2), 2
                        )
                    )
                ),
                description=fake.sentence(),
                quantity=fake.random_int(min=0, max=100),
            ),
        )
        items.append(item)
        print(f"  Created item: {item.name} (${item.cost})")

    return items


async def create_embeddings(session: AsyncSession, items: list[Item]) -> None:
    """Generate and store embeddings for seeded items."""
    settings = EmbeddingSettings()
    embedder = create_embedder(settings)
    for item in items:
        await session.refresh(item)
        name = item.name
        content = build_item_text(
            name=name,
            description=item.description,
            cost=item.cost,
            quantity=item.quantity,
        )
        await embed_and_store(
            session,
            source_type="item",
            source_id=item.id,
            content=content,
            embedder=embedder,
            metadata={"name": name},
        )
        print(f"  Embedded item: {name}")


def run_migrations() -> None:
    """Run alembic migrations (upgrade head)."""
    root = Path(__file__).resolve().parent.parent
    alembic_cfg = Config(str(root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied successfully.")


async def seed_database(
    session: AsyncSession, should_create_embeddings: bool = False
) -> None:
    """Run the full database seed."""
    await anyio.to_thread.run_sync(run_migrations)

    print("Creating users...")
    await create_users(session)

    print("\nCreating items...")
    items = await create_items(session)

    if should_create_embeddings:
        print("\nCreating embeddings...")
        await create_embeddings(session, items)

    print("\nDone! Database seeded successfully.")


async def drop_tables(session: AsyncSession) -> None:
    for table in {Item, Message, Conversation, RefreshToken, UserOAuthAccount, User}:
        await session.exec(delete(table))
        await session.commit()


async def _main(should_create_embeddings: bool = False) -> None:
    engine = create_db_engine()
    async with AsyncSession(engine) as session:
        await drop_tables(session)
        await seed_database(session)
    await destroy_engine(engine)


def main() -> None:
    """Sync entry point for the ``seed`` console script."""
    # TODO: Arg parse for should_create_embeddings
    anyio.run(_main)


if __name__ == "__main__":
    main()
