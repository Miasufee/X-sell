from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.crud import user_crud
from app.utils.responses.exceptions import Exceptions
from app.utils.responses.success import Success


router = APIRouter()


@router.get('/get/users')
async def get_users(db: AsyncSession = Depends(get_async_db)):
    result = await user_crud.get_multi(db)
    if not result:
        Exceptions.no_objects_found()
    return Success.ok(detail="Users retrieved successfully", users=result)