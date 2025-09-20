from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_base import CrudBase
from app.models import User


class UserCrud(CrudBase[User]):
    def __init__(self):
        super().__init__(User)

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.get(db, email=email)

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by id"""
        return await self.get(db, id=user_id)

    async def get_users(self, db: AsyncSession, skip: int = 0, limit: int = 100):
        """Get multiple users (basic pagination using skip/limit)"""
        return await self.get_multi(db, skip=skip, limit=limit)

    async def paginate_users(self, db: AsyncSession, page: int = 1, per_page: int = 20):
        """Get paginated users with metadata"""
        return await self.paginate(db, page=page, per_page=per_page)


user_crud = UserCrud()
