from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.user import EmailVerification
from app.services.auth.auth_utils import get_verification_code, verify_email

router = APIRouter()


@router.get("/get/verification/code/")
async def _get_verification_code(payload: EmailVerification, db: AsyncSession = Depends(get_async_db)):
    return await get_verification_code(db, payload.email)


@router.post("/verify/email/")
async def _verify_email(payload: EmailVerification, db: AsyncSession = Depends(get_async_db)):
    return await verify_email(db, payload.email, payload.verification_code)