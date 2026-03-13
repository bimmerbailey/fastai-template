import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic_ai import Agent

from fastai.agents.dependencies import AgentDeps
from fastai.agents.settings import AgentSettings
from fastai.auth.settings import AuthSettings
from fastai.auth.token_service import TokenError, TokenService
from fastai.users.models import User
from fastai.utils.dependencies import SessionDep

bearer_scheme = HTTPBearer()


def get_agent(request: Request) -> Agent[AgentDeps, str]:
    """Retrieve the agent instance from application state."""
    agent: Agent[AgentDeps, str] = request.app.state.agent
    return agent


def get_agent_settings(request: Request) -> AgentSettings:
    """Retrieve agent settings from application state."""
    settings: AgentSettings = request.app.state.agent_settings
    return settings


def get_auth_settings(request: Request) -> AuthSettings:
    """Retrieve auth settings from application state."""
    settings: AuthSettings = request.app.state.auth_settings
    return settings


def get_token_service(request: Request) -> TokenService:
    """Retrieve token service from application state."""
    token_service: TokenService = request.app.state.token_service
    return token_service


async def get_current_user(
    session: SessionDep,
    token_service: TokenService = Depends(get_token_service),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    """Extract and validate the access token from the Authorization header,
    then return the corresponding user."""
    try:
        payload = token_service.decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await User.get(session, uuid.UUID(payload.sub))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


AgentDep = Annotated[Agent[AgentDeps, str], Depends(get_agent)]
AgentSettingsDep = Annotated[AgentSettings, Depends(get_agent_settings)]
AuthSettingsDep = Annotated[AuthSettings, Depends(get_auth_settings)]
TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
