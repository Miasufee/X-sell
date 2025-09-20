from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.user_schema import LoginAPIResponse, SuperAdmin
from app.core.auth_service.auth_utils import login

router = APIRouter()

@router.post("/login", response_model=LoginAPIResponse)
async def login_super_admin(payload: SuperAdmin, db: AsyncSession = Depends(get_async_db)):
    return await login(
        db=db, email=payload.email, password=payload.password,
        unique_id=payload.unique_id
    )

