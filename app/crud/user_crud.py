from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CrudBase
from app.models import User


class UserCrud(CrudBase[User]):
    def __init__(self):
        super().__init__(User)

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.get(db, email=email)

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """ get user by id"""
        return await self.get(db, id=user_id)


user_crud = UserCrud()
