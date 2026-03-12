import pytest
from pydantic_ai import Agent, ModelResponse, ToolCallPart, models
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.agents.core import create_agent, get_usage_limits
from fastai.agents.dependencies import AgentDeps
from fastai.agents.settings import AgentSettings

models.ALLOW_MODEL_REQUESTS = False

pytestmark = pytest.mark.integration


def _extract_tool_names(result) -> list[str]:  # type: ignore[no-untyped-def]
    """Extract all tool call names from agent run messages."""
    tool_names: list[str] = []
    for msg in result.all_messages():
        if isinstance(msg, ModelResponse):
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    tool_names.append(part.tool_name)
    return tool_names


@pytest.mark.asyncio
async def test_agent_creation(agent_settings: AgentSettings) -> None:
    """Agent factory produces a configured agent."""
    agent = create_agent(agent_settings)
    assert isinstance(agent, Agent)


@pytest.mark.asyncio
async def test_agent_responds_to_simple_message(
    test_agent: Agent[AgentDeps, str],
    test_db_engine: AsyncEngine,
    agent_settings: AgentSettings,
) -> None:
    """Agent produces a response for a simple message using TestModel."""
    deps = AgentDeps(engine=test_db_engine, settings=agent_settings)

    result = await test_agent.run("Hello, how are you?", deps=deps)

    assert isinstance(result.output, str)
    assert len(result.output) > 0


@pytest.mark.asyncio
async def test_agent_calls_get_current_time_tool(
    test_agent: Agent[AgentDeps, str],
    test_db_engine: AsyncEngine,
    agent_settings: AgentSettings,
) -> None:
    """Agent calls the get_current_time tool and incorporates the result."""
    deps = AgentDeps(engine=test_db_engine, settings=agent_settings)

    result = await test_agent.run("What time is it?", deps=deps)

    assert isinstance(result.output, str)
    assert len(result.output) > 0
    tool_names = _extract_tool_names(result)
    assert "get_current_time" in tool_names


@pytest.mark.asyncio
async def test_agent_calls_search_items_tool(
    test_agent: Agent[AgentDeps, str],
    test_db_engine: AsyncEngine,
    agent_settings: AgentSettings,
) -> None:
    """Agent calls the search_items tool when asked about inventory."""
    deps = AgentDeps(engine=test_db_engine, settings=agent_settings)

    result = await test_agent.run("Search for widgets in the inventory", deps=deps)

    assert isinstance(result.output, str)
    tool_names = _extract_tool_names(result)
    assert "search_items" in tool_names


@pytest.mark.asyncio
async def test_agent_calls_get_item_count_tool(
    test_agent: Agent[AgentDeps, str],
    test_db_engine: AsyncEngine,
    agent_settings: AgentSettings,
) -> None:
    """Agent calls the get_item_count tool."""
    deps = AgentDeps(engine=test_db_engine, settings=agent_settings)

    result = await test_agent.run("How many items are in inventory?", deps=deps)

    assert isinstance(result.output, str)
    tool_names = _extract_tool_names(result)
    assert "get_item_count" in tool_names


def test_get_usage_limits(agent_settings: AgentSettings) -> None:
    """Usage limits are built from settings."""
    limits = get_usage_limits(agent_settings)
    assert limits.request_limit == agent_settings.request_limit
