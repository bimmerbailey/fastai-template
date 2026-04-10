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

When users ask about items, you have two search tools:
- search_items: for exact or partial name matches
- semantic_search: for conceptual or descriptive queries

Be concise, accurate, and helpful. Use the available tools to look up \
real data rather than guessing.\
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

    @agent.tool
    async def semantic_search(
        ctx: RunContext[AgentDeps],
        query: str,
        source_type: str | None = None,
    ) -> str:
        """Search for items using semantic similarity. Use this when the
        user's query is conceptual or descriptive rather than an exact name
        match (e.g. "something to keep warm" or "affordable electronics").

        Args:
            query: A natural language description of what to search for.
            source_type: Optional filter by source type (e.g. "item").
                Defaults to searching all source types.
        """
        async with AsyncSession(ctx.deps.engine) as session:
            results = await ctx.deps.knowledge_base.search(
                session,
                query=query,
                source_type=source_type,
                limit=5,
            )

        if not results:
            return f"No semantically similar results found for '{query}'."

        lines = [f"Found {len(results)} similar result(s):"]
        for r in results:
            lines.append(
                f"- [{r.source_type}:{r.source_id}] "
                f"{r.chunk_text[:200]} (similarity: {r.score:.2f})"
            )
        return "\n".join(lines)


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
