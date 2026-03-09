from typing import Annotated

from fastapi import Depends, Request
from pydantic_ai import Agent

from fastai.agents.dependencies import AgentDeps
from fastai.agents.settings import AgentSettings


def get_agent(request: Request) -> Agent[AgentDeps, str]:
    """Retrieve the agent instance from application state."""
    agent: Agent[AgentDeps, str] = request.app.state.agent
    return agent


def get_agent_settings(request: Request) -> AgentSettings:
    """Retrieve agent settings from application state."""
    settings: AgentSettings = request.app.state.agent_settings
    return settings


AgentDep = Annotated[Agent[AgentDeps, str], Depends(get_agent)]
AgentSettingsDep = Annotated[AgentSettings, Depends(get_agent_settings)]
