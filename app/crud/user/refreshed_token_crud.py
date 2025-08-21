from datetime import datetime, timezone
from typing import Optional, Sequence, Any, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_

from app.crud.base import CrudBase
from app.models.user import RefreshedToken


class RefreshedTokenCrud(CrudBase[RefreshedToken]):
    def __init__(self):
        super().__init__(RefreshedToken)

    async def create_refresh_token(
        self,
        db: AsyncSession,
        user_id: int,
        refresh_token: str,
        expires_at: datetime
    ) -> RefreshedToken:
        """Create a new refresh token"""
        return await self.create(
            db,
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

    async def get_valid_token(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> Optional[RefreshedToken]:
        """Get valid (non-expired) refresh token"""
        now = datetime.now(timezone.utc)
        where_clause = and_(
            RefreshedToken.refresh_token == refresh_token,
            RefreshedToken.expires_at > now
        )
        return await self.get(db, where_clause=where_clause)

    async def get_user_tokens(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Sequence[RefreshedToken]:
        """Get all refresh tokens for a user"""
        return await self.get_multi(
            db,
            user_id=user_id,
            order_by=RefreshedToken.created_at.desc()
        )

    async def delete_expired_tokens(self, db: AsyncSession) -> None:
        """Delete all expired refresh tokens and return count"""
        now = datetime.now(timezone.utc)
        where_clause = RefreshedToken.expires_at <= now
        return await self.delete(db, where_clause=where_clause)

    async def delete_user_tokens(
        self,
        db: AsyncSession,
        user_id: int
    ) -> None:
        """Delete all refresh tokens for a user and return count"""
        return await self.delete(db, user_id=user_id)

    async def revoke_token(
        self,
        db: AsyncSession,
        refresh_token: str
    ) -> None:
        """Revoke a specific refresh token and return count"""
        return await self.delete(db, refresh_token=refresh_token)


# Initialize token CRUD
refreshed_token_crud = RefreshedTokenCrud()