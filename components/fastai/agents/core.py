from datetime import datetime, timezone

import structlog.stdlib
from pydantic_ai import Agent, ModelSettings, RunContext, UsageLimits
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.agents.dependencies import AgentDeps
from fastai.agents.settings import AgentSettings
from fastai.chats.models import Message
from fastai.chats.schemas import MessageRole
from fastai.items import Item

logger = structlog.stdlib.get_logger(__name__)


INSTRUCTIONS = """\
You are a helpful AI assistant. You can answer general questions and help \
users look up items in the inventory database.

Be concise, accurate, and helpful. When users ask about items or inventory, \
use the available tools to look up real data rather than guessing.\
"""


def create_agent(settings: AgentSettings) -> Agent[AgentDeps, str]:
    """Create and configure the chat agent.

    Args:
        settings: Agent configuration settings.

    Returns:
        A configured PydanticAI agent ready for use.
    """
    agent = Agent[AgentDeps, str](
        model=settings.model,
        deps_type=AgentDeps,
        output_type=str,
        instructions=INSTRUCTIONS,
        model_settings=ModelSettings(
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout,
        ),
    )

    _register_tools(agent)

    logger.info("Agent created", model=settings.model)
    return agent


def _register_tools(agent: Agent[AgentDeps, str]) -> None:
    """Register all tools with the agent."""

    @agent.tool_plain
    def get_current_time() -> str:
        """Get the current date and time in UTC."""
        now = datetime.now(timezone.utc)
        return now.isoformat()

    @agent.tool
    async def search_items(
        ctx: RunContext[AgentDeps],
        query: str,
    ) -> str:
        """Search for items in the inventory database.

        Args:
            query: A search term to find matching items by name.
        """

        async with AsyncSession(ctx.deps.engine) as session:
            items = await Item.search_by_name(session, query)

        if not items:
            return f"No items found matching '{query}'."

        lines = [f"Found {len(items)} item(s):"]
        for item in items:
            cost_str = f"${item.cost}" if item.cost is not None else "N/A"
            lines.append(f"- {item.name} (qty: {item.quantity}, cost: {cost_str})")
        return "\n".join(lines)

    @agent.tool
    async def get_item_count(ctx: RunContext[AgentDeps]) -> str:
        """Get the total number of items in the inventory."""

        async with AsyncSession(ctx.deps.engine) as session:
            count = await Item.count(session)

        return f"There are {count} items in the inventory."


def get_usage_limits(settings: AgentSettings) -> UsageLimits:
    """Build usage limits from settings.

    Args:
        settings: Agent configuration settings.

    Returns:
        Configured usage limits for agent runs.
    """
    return UsageLimits(request_limit=settings.request_limit)


def messages_to_history(messages: list[Message]) -> list[ModelMessage]:
    """Convert persisted Message records to PydanticAI message history.

    Each ``Message`` becomes either a ``ModelRequest`` (user) or a
    ``ModelResponse`` (assistant) so that the agent receives full
    conversational context.

    Args:
        messages: Database message records ordered by creation time.

    Returns:
        A list of ``ModelMessage`` objects suitable for
        ``agent.run(message_history=...)``.
    """
    history: list[ModelMessage] = []
    for msg in messages:
        text = msg.content_text or ""
        if msg.role == MessageRole.USER:
            history.append(ModelRequest(parts=[UserPromptPart(content=text)]))
        else:
            history.append(ModelResponse(parts=[TextPart(content=text)]))
    return history
