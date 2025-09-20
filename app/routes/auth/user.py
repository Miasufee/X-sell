from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas import UserResponse, UserCreate, UserLogin
from app.schemas.user_schema import LoginAPIResponse
from app.core.auth_service.user_service import login_user, create_user

router = APIRouter()


@router.post("/create", response_model=UserResponse)
async def _create_user(login_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
     return await create_user(db, login_data.email)


@router.post("/login", response_model=LoginAPIResponse)
async def _login_user(login_data: UserLogin, db: AsyncSession = Depends(get_async_db)):
    return await login_user(db, login_data.email, login_data.verification_code)



