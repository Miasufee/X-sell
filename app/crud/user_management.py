from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from app.utils.responses.exceptions import Exceptions
from ..models import User, VerificationCode, RefreshToken
from .base import CrudBase


class UserCrud(CrudBase[User]):

    def __init__(self):
        super().__init__(User)

    async def get_user_by_email(self, db: AsyncSession, email: str):
        result = await db.execute(select(self.model).where(self.model.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, db: AsyncSession, user_id: int):
        result = await db.execute(select(self.model).where(self.model.id == user_id))
        return result.scalar_one_or_none()


user_crud = UserCrud()


class RefreshTokenCrud(CrudBase[RefreshToken]):
    def __init__(self):
        super().__init__(RefreshToken)

    async def get_refresh_token(self, db: AsyncSession, token: str) -> Optional[RefreshToken]:
        try:
            result = await db.execute(select(self.model).filter(self.model.token == token))
            return result.scalars().first()
        except SQLAlchemyError as e:
            print(f"Error getting refresh token: {e}")
            return None


refresh_token_crud = RefreshTokenCrud()


class VerificationCodeCrud(CrudBase[VerificationCode]):
    def __init__(self):
        super().__init__(VerificationCode)

    async def get_verification_code(self, db: AsyncSession, user_id: int) -> Optional[VerificationCode]:
        result = await db.execute(select(self.model).where(self.model.user_id == user_id))
        return result.scalars().first()

    async def delete_verification_code(self, db: AsyncSession, user_id: int) -> bool:
        try:
            await db.execute(delete(self.model).where(self.model.user_id == user_id))
            await db.commit()
            return True
        except SQLAlchemyError as e:
            await db.rollback()
            return False

    async def verify_code(self, db: AsyncSession, user_id: int, code: str) -> bool:
        try:
            result = await db.execute(
                select(self.model).where(
                    self.model.user_id == user_id,
                    self.model.code == str(code),
                    self.model.expires_at > datetime.utcnow()
                )
            )
            db_code = result.scalars().first()
            if db_code:
                await db.delete(db_code)
                await db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            await db.rollback()
            return False


verification_code_crud = VerificationCodeCrud()
