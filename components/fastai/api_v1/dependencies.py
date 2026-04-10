import uuid
from typing import Annotated

import structlog.contextvars
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from pydantic_ai import Agent

from fastai.agents.dependencies import AgentDeps
from fastai.agents.settings import AgentSettings
from fastai.auth.settings import AuthSettings
from fastai.auth.token_service import TokenError, TokenService
from fastai.embeddings.core import KnowledgeBase
from fastai.users.models import User
from fastai.utils.dependencies import SessionDep

security_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scopes={
        "admin": "Full administrative access.",
    },
    auto_error=False,
)


def get_agent(request: Request) -> Agent[AgentDeps, str]:
    """Retrieve the agent instance from application state."""
    agent: Agent[AgentDeps, str] = request.app.state.agent
    return agent


def get_agent_settings(request: Request) -> AgentSettings:
    """Retrieve agent settings from application state."""
    settings: AgentSettings = request.app.state.agent_settings
    return settings


def get_knowledge_base(request: Request) -> KnowledgeBase:
    """Retrieve the KnowledgeBase from application state."""
    kb: KnowledgeBase = request.app.state.knowledge_base
    return kb


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
    token: str | None = Depends(security_scheme),
) -> User:
    """Extract and validate the access token from the Authorization header,
    then return the corresponding user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = token_service.decode_access_token(token=token)
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


async def get_scoped_user(
    security_scopes: SecurityScopes,
    session: SessionDep,
    token_service: TokenService = Depends(get_token_service),
    token: str | None = Depends(security_scheme),
) -> User:
    """Extract and validate the access token, checking OAuth2 scopes.

    When used via ``Security(..., scopes=[...])``, the required scopes are
    checked against the scopes embedded in the JWT.
    """
    authenticate_value = "Bearer"
    if security_scopes.scopes:
        authenticate_value += f' scope="{security_scopes.scope_str}"'

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token.",
            headers={"WWW-Authenticate": authenticate_value},
        )

    try:
        payload = token_service.decode_access_token(token=token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
            headers={"WWW-Authenticate": authenticate_value},
        )

    user = await User.get(session, uuid.UUID(payload.sub))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": authenticate_value},
        )

    for scope in security_scopes.scopes:
        if scope not in payload.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions.",
                headers={"WWW-Authenticate": authenticate_value},
            )

    structlog.contextvars.bind_contextvars(actor=user.id)
    # TODO: Think about returning a plain BaseModel instead of a data model
    return user


AgentDep = Annotated[Agent[AgentDeps, str], Depends(get_agent)]
AgentSettingsDep = Annotated[AgentSettings, Depends(get_agent_settings)]
KnowledgeBaseDep = Annotated[KnowledgeBase, Depends(get_knowledge_base)]
AuthSettingsDep = Annotated[AuthSettings, Depends(get_auth_settings)]
TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]
CurrentUserDep = Annotated[User, Security(get_scoped_user)]
CurrentAdminDep = Annotated[User, Security(get_scoped_user, scopes=["admin"])]
