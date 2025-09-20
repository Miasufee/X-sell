from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.user_schema import EmailVerification, PasswordResetPayloadRequest, ResetOtp, PasswordResetPayload
from app.core.auth_service.auth_utils import get_verification_code, verify_email, request_password_reset, \
    verify_reset_code, reset_password_with_otp

router = APIRouter()


@router.get("/get/verification/code/")
async def _get_verification_code(payload: EmailVerification, db: AsyncSession = Depends(get_async_db)):
    return await get_verification_code(db, payload.email)


@router.post("/verify/email/")
async def _verify_email(payload: EmailVerification, db: AsyncSession = Depends(get_async_db)):
    return await verify_email(db, payload.email, payload.verification_code)

@router.post("/reset/password/")
async def _reset_admin_password(payload: PasswordResetPayloadRequest, db: AsyncSession = Depends(get_async_db)):
    return await request_password_reset(db, payload.email, payload.unique_id, payload.superuser_secret_key)

@router.post("/otp")
async def _verify_reset_code(payload: EmailVerification, db: AsyncSession = Depends(get_async_db)):
    return await verify_reset_code(db, payload.email, payload.verification_code)


@router.post("/reset/with/otp/")
async def _reset_with_otp(payload: ResetOtp, db: AsyncSession = Depends(get_async_db)):
    return await reset_password_with_otp(db, payload.email, payload.otp, payload.password)