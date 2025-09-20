from typing import Optional, Sequence
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, delete
from app.crud.crud_base import CrudBase
from app.models.user import VerificationCode


class VerificationCodeCrud(CrudBase[VerificationCode]):
    def __init__(self):
        super().__init__(VerificationCode)

    async def create_verification_code(
            self,
            db: AsyncSession,
            user_id: int,
            code: str,
            expires_at: datetime  # Changed to accept datetime directly
    ) -> VerificationCode:
        """Create a new verification code with expiration"""
        return await self.create(
            db,
            user_id=user_id,
            code=code,
            expires_at=expires_at
        )

    async def get_valid_code(
            self,
            db: AsyncSession,
            user_id: int,
            code: str
    ) -> Optional[VerificationCode]:
        """Get valid (non-expired) verification code"""
        now = datetime.now(timezone.utc)
        where_clause = and_(
            VerificationCode.user_id == user_id,
            VerificationCode.code == code,
            VerificationCode.expires_at > now
        )
        return await self.get(db, where_clause=where_clause)

    async def delete_code(
            self,
            db: AsyncSession,
            user_id: int,
            code: str
    ) -> None:
        """Delete a specific verification code"""
        await db.execute(
            delete(VerificationCode).where(
                and_(
                    VerificationCode.user_id == user_id,
                    VerificationCode.code == code
                )
            )
        )
        await db.commit()


    async def get_verification_code(
        self,
        db: AsyncSession,
        user_id: int
    ) -> Optional[VerificationCode]:
        """Get verification code for a user"""
        return await self.get(db, user_id=user_id)

    async def validate_code(
        self,
        db: AsyncSession,
        user_id: int,
        code: str
    ) -> bool:
        """Validate a verification code and delete it if used"""
        valid_code = await self.get_valid_code(db, user_id, code)
        if valid_code:
            await self.delete(db, id=valid_code.id)
            return True
        return False


    async def get_user_codes(self, db: AsyncSession, user_id: int) -> Sequence[VerificationCode]:
        """Get all verification codes for a user"""
        return await self.get_multi(db, user_id=user_id, order_by=VerificationCode.created_at.desc())

    async def delete_expired_codes(self, db: AsyncSession) -> None:
        """Delete all expired verification codes"""
        now = datetime.now(timezone.utc)
        where_clause = VerificationCode.expires_at <= now
        await self.delete(db, where_clause=where_clause)

    async def delete_user_codes(self, db: AsyncSession, user_id: int) -> None:
        """Delete all verification codes for a user"""
        await self.delete(db, user_id=user_id)

    async def get_latest_code(self, db: AsyncSession, user_id: int) -> Optional[VerificationCode]:
        """Get the latest verification code for a user"""
        codes = await self.get_multi(
            db,
            user_id=user_id,
            limit=1,
            order_by=VerificationCode.created_at.desc()
        )
        return codes[0] if codes else None

    async def code_exists(self, db: AsyncSession, user_id: int, code: str) -> bool:
        """Check if verification code exists for user"""
        return await self.exists(db, user_id=user_id, code=code)


verification_code_crud = VerificationCodeCrud()