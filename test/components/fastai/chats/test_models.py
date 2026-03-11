import uuid

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.auth.core import PasswordService
from fastai.chats.models import Conversation, Message
from fastai.chats.schemas import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
    MessageRole,
)
from fastai.users.models import User
from fastai.users.schemas import UserCreate

pytestmark = pytest.mark.integration


@pytest.fixture
def hasher() -> PasswordService:
    return PasswordService()


@pytest_asyncio.fixture
async def sample_user(test_db_session: AsyncSession, hasher: PasswordService) -> User:
    """Create a sample user for tests that need an existing record."""
    user_in = UserCreate(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password="securepassword123",
    )
    return await User.create(test_db_session, user_in, hasher=hasher)


@pytest_asyncio.fixture
async def sample_conversation(
    test_db_session: AsyncSession, sample_user: User
) -> Conversation:
    """Create a sample conversation for tests that need an existing record."""
    assert sample_user.id is not None
    conv_in = ConversationCreate(
        user_id=sample_user.id,
        title="Test Conversation",
    )
    return await Conversation.create(test_db_session, conv_in)


@pytest_asyncio.fixture
async def sample_message(
    test_db_session: AsyncSession, sample_conversation: Conversation
) -> Message:
    """Create a sample message for tests that need an existing record."""
    assert sample_conversation.id is not None
    msg_in = MessageCreate(
        conversation_id=sample_conversation.id,
        role=MessageRole.USER,
        content_text="Hello, assistant!",
    )
    return await Message.create(test_db_session, msg_in)


# ── Conversation Tests ──


@pytest.mark.asyncio
async def test_create_conversation(
    test_db_session: AsyncSession, sample_user: User
) -> None:
    assert sample_user.id is not None
    user_id = sample_user.id
    conv_in = ConversationCreate(
        user_id=user_id,
        title="My Chat",
    )

    conv = await Conversation.create(test_db_session, conv_in)

    assert conv.id is not None
    assert conv.user_id == user_id
    assert conv.title == "My Chat"
    assert conv.created_at is not None
    assert conv.updated_at is not None


@pytest.mark.asyncio
async def test_create_conversation_no_title(
    test_db_session: AsyncSession, sample_user: User
) -> None:
    assert sample_user.id is not None
    conv_in = ConversationCreate(user_id=sample_user.id)

    conv = await Conversation.create(test_db_session, conv_in)

    assert conv.id is not None
    assert conv.title is None


@pytest.mark.asyncio
async def test_get_conversation(
    test_db_session: AsyncSession, sample_conversation: Conversation
) -> None:
    assert sample_conversation.id is not None
    fetched = await Conversation.get(test_db_session, sample_conversation.id)

    assert fetched is not None
    assert fetched.id == sample_conversation.id
    assert fetched.title == sample_conversation.title


@pytest.mark.asyncio
async def test_get_conversation_not_found(test_db_session: AsyncSession) -> None:
    fetched = await Conversation.get(test_db_session, uuid.uuid4())

    assert fetched is None


@pytest.mark.asyncio
async def test_get_by_user(test_db_session: AsyncSession, sample_user: User) -> None:
    assert sample_user.id is not None
    user_id = sample_user.id
    for i in range(3):
        await Conversation.create(
            test_db_session,
            ConversationCreate(user_id=user_id, title=f"Chat {i}"),
        )

    conversations = await Conversation.get_by_user(test_db_session, user_id)

    assert len(conversations) == 3


@pytest.mark.asyncio
async def test_get_by_user_pagination(
    test_db_session: AsyncSession, sample_user: User
) -> None:
    assert sample_user.id is not None
    user_id = sample_user.id
    for i in range(5):
        await Conversation.create(
            test_db_session,
            ConversationCreate(user_id=user_id, title=f"Chat {i}"),
        )

    page = await Conversation.get_by_user(test_db_session, user_id, offset=2, limit=2)

    assert len(page) == 2


@pytest.mark.asyncio
async def test_get_by_user_newest_first(
    test_db_session: AsyncSession, sample_user: User
) -> None:
    assert sample_user.id is not None
    user_id = sample_user.id
    first = await Conversation.create(
        test_db_session,
        ConversationCreate(user_id=user_id, title="First"),
    )
    second = await Conversation.create(
        test_db_session,
        ConversationCreate(user_id=user_id, title="Second"),
    )

    conversations = await Conversation.get_by_user(test_db_session, user_id)

    assert conversations[0].id == second.id
    assert conversations[1].id == first.id


@pytest.mark.asyncio
async def test_update_conversation(
    test_db_session: AsyncSession, sample_conversation: Conversation
) -> None:
    update_in = ConversationUpdate(title="Renamed Chat")

    updated = await sample_conversation.update(test_db_session, update_in)

    assert updated.id == sample_conversation.id
    assert updated.title == "Renamed Chat"


@pytest.mark.asyncio
async def test_delete_conversation(
    test_db_session: AsyncSession, sample_conversation: Conversation
) -> None:
    assert sample_conversation.id is not None
    conv_id = sample_conversation.id

    await sample_conversation.delete(test_db_session)

    fetched = await Conversation.get(test_db_session, conv_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_conversation_cascades_messages(
    test_db_session: AsyncSession,
    sample_conversation: Conversation,
) -> None:
    assert sample_conversation.id is not None
    conv_id = sample_conversation.id

    msg = await Message.create(
        test_db_session,
        MessageCreate(
            conversation_id=conv_id,
            role=MessageRole.USER,
            content_text="This should be deleted",
        ),
    )
    assert msg.id is not None
    msg_id = msg.id

    await sample_conversation.delete(test_db_session)

    fetched_msg = await Message.get(test_db_session, msg_id)
    assert fetched_msg is None


# ── Message Tests ──


@pytest.mark.asyncio
async def test_create_message(
    test_db_session: AsyncSession, sample_conversation: Conversation
) -> None:
    assert sample_conversation.id is not None
    conv_id = sample_conversation.id
    msg_in = MessageCreate(
        conversation_id=conv_id,
        role=MessageRole.USER,
        content_text="Hello!",
    )

    msg = await Message.create(test_db_session, msg_in)

    assert msg.id is not None
    assert msg.conversation_id == conv_id
    assert msg.role == MessageRole.USER
    assert msg.content_text == "Hello!"
    assert msg.created_at is not None


@pytest.mark.asyncio
async def test_create_message_assistant_role(
    test_db_session: AsyncSession, sample_conversation: Conversation
) -> None:
    assert sample_conversation.id is not None
    msg_in = MessageCreate(
        conversation_id=sample_conversation.id,
        role=MessageRole.ASSISTANT,
        content_text="Hi, how can I help?",
    )

    msg = await Message.create(test_db_session, msg_in)

    assert msg.role == MessageRole.ASSISTANT
    assert msg.content_text == "Hi, how can I help?"


@pytest.mark.asyncio
async def test_get_message(
    test_db_session: AsyncSession, sample_message: Message
) -> None:
    assert sample_message.id is not None
    fetched = await Message.get(test_db_session, sample_message.id)

    assert fetched is not None
    assert fetched.id == sample_message.id
    assert fetched.content_text == sample_message.content_text


@pytest.mark.asyncio
async def test_get_message_not_found(test_db_session: AsyncSession) -> None:
    fetched = await Message.get(test_db_session, uuid.uuid4())

    assert fetched is None


@pytest.mark.asyncio
async def test_get_by_conversation(
    test_db_session: AsyncSession, sample_conversation: Conversation
) -> None:
    assert sample_conversation.id is not None
    conv_id = sample_conversation.id

    await Message.create(
        test_db_session,
        MessageCreate(
            conversation_id=conv_id, role=MessageRole.USER, content_text="First"
        ),
    )
    await Message.create(
        test_db_session,
        MessageCreate(
            conversation_id=conv_id, role=MessageRole.ASSISTANT, content_text="Second"
        ),
    )
    await Message.create(
        test_db_session,
        MessageCreate(
            conversation_id=conv_id, role=MessageRole.USER, content_text="Third"
        ),
    )

    messages = await Message.get_by_conversation(test_db_session, conv_id)

    assert len(messages) == 3
    assert messages[0].content_text == "First"
    assert messages[1].content_text == "Second"
    assert messages[2].content_text == "Third"


@pytest.mark.asyncio
async def test_get_by_conversation_pagination(
    test_db_session: AsyncSession, sample_conversation: Conversation
) -> None:
    assert sample_conversation.id is not None
    conv_id = sample_conversation.id

    for i in range(5):
        await Message.create(
            test_db_session,
            MessageCreate(
                conversation_id=conv_id,
                role=MessageRole.USER,
                content_text=f"Message {i}",
            ),
        )

    page = await Message.get_by_conversation(
        test_db_session, conv_id, offset=2, limit=2
    )

    assert len(page) == 2


@pytest.mark.asyncio
async def test_get_by_conversation_ordered_by_created_at(
    test_db_session: AsyncSession, sample_conversation: Conversation
) -> None:
    assert sample_conversation.id is not None
    conv_id = sample_conversation.id

    first = await Message.create(
        test_db_session,
        MessageCreate(
            conversation_id=conv_id, role=MessageRole.USER, content_text="First"
        ),
    )
    second = await Message.create(
        test_db_session,
        MessageCreate(
            conversation_id=conv_id, role=MessageRole.ASSISTANT, content_text="Second"
        ),
    )

    messages = await Message.get_by_conversation(test_db_session, conv_id)

    assert messages[0].id == first.id
    assert messages[1].id == second.id


@pytest.mark.asyncio
async def test_delete_message(
    test_db_session: AsyncSession, sample_message: Message
) -> None:
    assert sample_message.id is not None
    msg_id = sample_message.id

    await sample_message.delete(test_db_session)

    fetched = await Message.get(test_db_session, msg_id)
    assert fetched is None
