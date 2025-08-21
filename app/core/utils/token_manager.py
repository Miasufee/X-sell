from datetime import datetime, UTC
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils.generate import Token
from app.core.utils.response.exceptions import Exceptions
from app.crud.user_management import refreshed_token_crud
from app.models.user.user import User
from app.core.security import SecurityManager


class TokenManager:

    @staticmethod
    async def create_tokens(
            db: AsyncSession,
            user: User,
            token_version: int = 1
    ) -> Tuple[Token, datetime]:
        """
        Create and store token pair for a user

        Args:
            db: AsyncSession - database session
            user: User - user model instance
            token_version: int - current token version

        Returns:
            Tuple[Token, datetime]: Token pair and refresh token expiration
        """
        access_token = SecurityManager.create_access_token(user.id, token_version)
        refresh_token = SecurityManager.create_refresh_token(user.id, token_version)

        # Calculate refresh token expiration
        from app.core.config import settings
        from datetime import datetime, timedelta
        refresh_expires = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)


        # Create Token object
        tokens = Token(
            access_token=access_token,
            refresh_token=refresh_token
        )

        # Store refresh token
        await refreshed_token_crud.create_refresh_token(
            db,
            user_id=user.id,
            refresh_token=tokens.refresh_token,
            expires_at=refresh_expires
        )

        return tokens, refresh_expires

    async def refresh_tokens(
            self,
            db: AsyncSession,
            refresh_token: str,
            current_user: User
    ) -> Tuple[Token, datetime]:
        """
        Refresh token pair with rotation

        Args:
            db: AsyncSession - database session
            refresh_token: str - current refresh token
            current_user: User - authenticated user

        Returns:
            Tuple[Token, datetime]: New token pair and expiration
        """
        # Verify refresh token is valid
        token_record = await refreshed_token_crud.get_valid_token(db, refresh_token)
        if not token_record:
            raise ValueError("Invalid refresh token")

        # Revoke old refresh token
        await refreshed_token_crud.revoke_token(db, refresh_token)

        # Create new tokens with same version
        return await self.create_tokens(db, current_user, current_user.token_version)

    @staticmethod
    async def verify_access_token(
            db: AsyncSession,
            token: str,
            require_active: bool = True
    ) -> Optional[User]:
        """
        Verify access token and return associated user

        Args:
            db: AsyncSession - database session
            token: str - JWT access token
            require_active: bool - check user active status

        Returns:
            Optional[User]: Authenticated user if valid
        """
        try:
            from fastapi import Request
            from unittest.mock import Mock

            # Create a mock request with the token in cookies for SecurityManager
            mock_request = Mock(spec=Request)
            mock_request.cookies = {"access_token": token}
            mock_request.headers = {}

            user = await SecurityManager.get_current_user(request=mock_request, db=db)

            if require_active and not user.is_active:
                return None

            return user

        except Exceptions.bad_request():
            return None

    @staticmethod
    async def revoke_all_tokens(
            db: AsyncSession,
            user: User,
            increment_version: bool = True
    ) -> None:
        """
        Revoke all tokens for a user

        Args:
            db: AsyncSession - database session
            user: User - target user
            increment_version: bool - increment token version
        """
        if increment_version:
            user.token_version += 1
            db.add(user)
            await db.commit()

        await refreshed_token_crud.delete_user_tokens(db, user.id)

    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """
        Clean up expired tokens

        Args:
            db: AsyncSession - database session

        Returns:
            int: Number of tokens deleted
        """
        return await refreshed_token_crud.delete_expired_tokens(db)


# Initialize token manager
token_manager = TokenManager()
