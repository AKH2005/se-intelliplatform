"""Authentication Service handling user registration, credential verification, and token issuance."""

import logging
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import UserLoginRequest, UserRegisterRequest

logger = logging.getLogger(__name__)


class AuthService:
    """Orchestrates persistent user authentication and session management."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by normalized email."""
        stmt = select(User).where(User.email == email.strip().lower())
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch user by UUID."""
        stmt = select(User).where(User.id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def register(self, data: UserRegisterRequest) -> tuple[User, str]:
        """Register a new user account and issue an access token.

        Raises:
            ConflictError: If email is already registered.
        """
        existing = await self.get_by_email(data.email)
        if existing:
            raise ConflictError(
                f"An account with email '{data.email}' already exists.",
                field="email",
                value=data.email,
            )

        hashed_pw = get_password_hash(data.password)
        new_user = User(
            id=uuid.uuid4(),
            email=data.email.strip().lower(),
            name=data.name.strip(),
            hashed_password=hashed_pw,
            role=UserRole.USER,
            is_active=True,
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        token = create_access_token({
            "sub": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role.value,
        })
        logger.info(f"Registered new user account: {new_user.email} [{new_user.id}]")
        return new_user, token

    async def authenticate(self, data: UserLoginRequest) -> tuple[User, str]:
        """Verify user credentials and issue an access token.

        Raises:
            UnauthorizedError: If email not found or password incorrect.
        """
        user = await self.get_by_email(data.email)
        if not user or not user.is_active:
            logger.warning(f"Failed authentication attempt for: {data.email}")
            raise UnauthorizedError("Invalid email or password.")

        if not verify_password(data.password, user.hashed_password):
            logger.warning(f"Failed password check for user: {data.email}")
            raise UnauthorizedError("Invalid email or password.")

        token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
        })
        logger.info(f"User authenticated successfully: {user.email} [{user.id}]")
        return user, token
