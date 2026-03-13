from __future__ import annotations

import uuid
from typing import Annotated

import structlog.stdlib
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.params import Body
from fastapi.security import OAuth2PasswordRequestForm

from fastai.api_v1.dependencies import AuthSettingsDep, TokenServiceDep
from fastai.auth.models import RefreshToken
from fastai.auth.schemas import TokenResponse
from fastai.auth.settings import AuthSettings
from fastai.auth.token_service import TokenError, TokenService
from fastai.users.exceptions import (
    UserInvalidCredentials,
    UserLockedError,
    UserNotFoundError,
    UserStatusError,
)
from fastai.users.models import User
from fastai.users.schemas import UserCreate
from fastai.utils.dependencies import SessionDep

logger = structlog.stdlib.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    if request.client is not None:
        return request.client.host
    return None


def _set_refresh_cookie(
    response: Response,
    refresh_token: str,
    max_age_days: int,
    settings: AuthSettings,
) -> None:
    """Set the refresh token as an HttpOnly cookie on the response."""
    response.set_cookie(
        key=settings.cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path=settings.cookie_path,
        max_age=max_age_days * 86400,
    )


def _clear_refresh_cookie(response: Response, settings: AuthSettings) -> None:
    """Delete the refresh token cookie."""
    response.delete_cookie(
        key=settings.cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path=settings.cookie_path,
    )


async def _issue_tokens(
    session: SessionDep,
    user: User,
    token_service: TokenService,
    response: Response,
    auth_settings: AuthSettings,
) -> TokenResponse:
    """Create an access/refresh token pair, persist the refresh token hash,
    and set the refresh token as an HttpOnly cookie."""
    assert user.id is not None

    access_token = token_service.create_access_token(user.id, is_admin=user.is_admin)
    refresh_token = token_service.create_refresh_token(user.id)

    # Decode the refresh token to get its expiry for DB storage
    payload = token_service.decode_refresh_token(refresh_token)

    await RefreshToken.create(
        session,
        user_id=user.id,
        token_hash=TokenService.hash_token(refresh_token),
        expires_at=payload.exp,
    )

    _set_refresh_cookie(
        response,
        refresh_token,
        max_age_days=auth_settings.refresh_token_expire_days,
        settings=auth_settings,
    )

    return TokenResponse(access_token=access_token)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    response: Response,
    session: SessionDep,
    user_in: Annotated[UserCreate, Body()],
    auth_settings: AuthSettingsDep,
    token_service: TokenServiceDep,
) -> TokenResponse:
    """Register a new user and return an access token.

    The refresh token is set as an HttpOnly cookie.
    """
    existing = await User.get_by_email(session, user_in.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user = await User.create(session, user_in)

    logger.info("User registered", user_id=str(user.id), email=user.email)
    return await _issue_tokens(session, user, token_service, response, auth_settings)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    session: SessionDep,
    auth_settings: AuthSettingsDep,
    token_service: TokenServiceDep,
    credentials: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    """Authenticate with email and password, returning an access token.

    The refresh token is set as an HttpOnly cookie.
    """

    client_ip = _get_client_ip(request)

    try:
        user = await User.login(
            session=session,
            email=credentials.username,
            password=credentials.password,
            auth_settings=auth_settings,
            ip_address=client_ip,
        )
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except UserLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e),
        )
    except UserStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except UserInvalidCredentials as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    return await _issue_tokens(session, user, token_service, response, auth_settings)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    session: SessionDep,
    auth_settings: AuthSettingsDep,
    token_service: TokenServiceDep,
    #  TODO: Look into removing this. It hard-codes cookie name.
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
) -> TokenResponse:
    """Exchange a valid refresh token (from cookie) for a new access token.

    The old refresh token is revoked and a new one is issued (rotation).
    """
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie is missing.",
        )

    # Decode and validate the refresh JWT
    try:
        payload = token_service.decode_refresh_token(refresh_token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
        )

    # Look up the stored token by hash
    token_hash = TokenService.hash_token(refresh_token)
    stored_token = await RefreshToken.get_by_token_hash(session, token_hash)
    if stored_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found.",
        )

    if stored_token.is_revoked:
        # Possible token reuse attack — revoke all tokens for this user
        logger.warning(
            "Revoked refresh token reuse detected",
            user_id=str(stored_token.user_id),
        )
        await RefreshToken.revoke_all_for_user(session, stored_token.user_id)
        _clear_refresh_cookie(response, auth_settings)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked.",
        )

    # Revoke the old token (rotation)
    await stored_token.revoke(session)

    # Verify the user still exists and is active
    user = await User.get(session, uuid.UUID(payload.sub))
    if user is None or not user.is_active:
        _clear_refresh_cookie(response, auth_settings)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    logger.info("Token refreshed", user_id=str(user.id))
    return await _issue_tokens(session, user, token_service, response, auth_settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: SessionDep,
    auth_settings: AuthSettingsDep,
    token_service: TokenServiceDep,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
) -> None:
    """Revoke a refresh token (from cookie), effectively logging the user out.

    This endpoint is idempotent — calling it with an already-revoked or
    unknown token returns 204 without error.
    """

    # Always clear the cookie regardless of token validity
    _clear_refresh_cookie(response, auth_settings)

    if refresh_token is None:
        return

    # Decode to validate it's a well-formed refresh token
    try:
        token_service.decode_refresh_token(refresh_token)
    except TokenError:
        # Even if the token is expired or malformed, we still try to revoke
        # by hash in case it exists in the DB
        pass

    token_hash = TokenService.hash_token(refresh_token)
    stored_token = await RefreshToken.get_by_token_hash(session, token_hash)
    if stored_token is not None and not stored_token.is_revoked:
        await stored_token.revoke(session)
        logger.info("User logged out", user_id=str(stored_token.user_id))
