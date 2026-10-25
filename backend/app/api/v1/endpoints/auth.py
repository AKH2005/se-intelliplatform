"""Authentication REST Endpoints for Registration, Login, Session Validation, and Logout."""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account and obtain access token",
)
async def register(
    data: UserRegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user account with validated credentials."""
    auth_service = AuthService(session=session)
    user, token = await auth_service.register(data)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and obtain JWT access token",
)
async def login(
    data: UserLoginRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email and password to receive a Bearer token."""
    auth_service = AuthService(session=session)
    user, token = await auth_service.authenticate(data)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get profile of the currently authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return profile details of the active authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Terminate user session",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Logout current user session."""
    logger.info(f"User session terminated: {current_user.email} [{current_user.id}]")
    return {"status": "SUCCESS", "message": "Successfully logged out."}
