import structlog.stdlib
from fastapi import APIRouter

from fastai.agents.core import get_usage_limits
from fastai.agents.dependencies import AgentDeps
from fastai.agents.schemas import ChatRequest, ChatResponse, ChatUsage
from fastai.api_v1.dependencies import AgentDep, AgentSettingsDep
from fastai.utils.dependencies import EngineDep

logger = structlog.stdlib.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    agent: AgentDep,
    settings: AgentSettingsDep,
    engine: EngineDep,
) -> ChatResponse:
    """Send a message to the AI chat agent and receive a response."""
    logger.info("Chat request received", message_length=len(chat_request.message))

    deps = AgentDeps(engine=engine, settings=settings)
    usage_limits = get_usage_limits(settings)

    result = await agent.run(
        chat_request.message,
        deps=deps,
        usage_limits=usage_limits,
    )

    run_usage = result.usage()
    usage = ChatUsage(
        input_tokens=run_usage.input_tokens,
        output_tokens=run_usage.output_tokens,
        requests=run_usage.requests,
    )

    logger.info(
        "Chat response generated",
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        requests=usage.requests,
    )

    return ChatResponse(
        message=result.output,
        model=settings.model,
        usage=usage,
    )
