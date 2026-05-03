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

logger = structlog.stdlib.get_logger(__name__)


INSTRUCTIONS = """\
You are a helpful AI assistant with access to a knowledge base of documents.

You MUST use the search_documents tool to answer questions about uploaded \
documents, files, or any domain-specific knowledge. Do not guess or \
hallucinate answers — always search first.

When a user asks a question that could be answered by their documents, \
search for relevant content before responding. If no results are found, \
let the user know.

Be concise, accurate, and helpful.\
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

    # TODO: Should this return structured data?
    @agent.tool
    async def search_documents(
        ctx: RunContext[AgentDeps],
        query: str,
    ) -> str:
        """Search uploaded documents for relevant information. Use this tool
        whenever the user asks a question that could be answered by their
        documents or files. Always search before answering domain-specific
        questions.

        Args:
            query: A natural language description of what to search for.
        """
        async with AsyncSession(ctx.deps.engine) as session:
            results = await ctx.deps.knowledge_base.search(
                session,
                query=query,
                source_type="document",
                limit=5,
            )

        if not results:
            return f"No relevant documents found for '{query}'."

        lines = [f"Found {len(results)} relevant passage(s):"]
        for r in results:
            source = r.metadata.get("filename", "unknown") if r.metadata else "unknown"
            lines.append(
                f"- [Source: {source}] {r.chunk_text} (relevance: {r.score:.2f})"
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
