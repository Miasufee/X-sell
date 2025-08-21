from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CrudBase
from app.models import User, UserRole


class UserCrud(CrudBase[User]):
    def __init__(self):
        super().__init__(User)

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.get_one(db, email=email)

    async def get_by_unique_id(self, db: AsyncSession, unique_id: str) -> Optional[User]:
        """Get user by unique_id"""
        return await self.get_one(db, unique_id=unique_id)

    async def get__user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """ get user by id"""
        return await self.get_one(db, id=user_id)

    async def update_password(self, db: AsyncSession, user_id: int, hashed_password: str) -> User:
        """Update user password"""
        return await self.update_by_id(db, obj_id=user_id, hashed_password=hashed_password)

    async def verify_email(self, db: AsyncSession, user_id: int) -> User:
        """Mark user email as verified"""
        return await self.update_by_id(db, obj_id=user_id, is_email_verified=True)

    async def approve_user(self, db: AsyncSession, user_id: int) -> User:
        """Approve user by admin"""
        return await self.update_by_id(db, obj_id=user_id, admin_approval=True)

    async def update_role(self, db: AsyncSession, user_id: int, role: UserRole) -> User:
        """Update user role"""
        return await self.update_by_id(db, obj_id=user_id, role=role)



user_crud = UserCrud()
