from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.user import LoginAPIResponse, SuperAdmin, PasswordResetPayload, EmailVerification, ResetOtp, \
    PasswordResetPayloadRequest
from app.services.auth.auth_utils import login, request_password_reset, verify_reset_code, reset_password_with_otp
import logging
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login", response_model=LoginAPIResponse)
async def login_super_admin(payload: SuperAdmin, db: AsyncSession = Depends(get_async_db)):
    logger.info("Login request payload: %s", payload.dict())
    return await login(
        db=db, email=payload.email, password=payload.password,
        unique_id=payload.unique_id
    )

@router.post("/reset/password/")
async def _reset_admin_password(payload:PasswordResetPayloadRequest, db: AsyncSession = Depends(get_async_db)):
    return await request_password_reset(db, payload.email, payload.unique_id)

@router.post("/otp")
async def _verify_reset_code(payload: EmailVerification, db: AsyncSession = Depends(get_async_db)):
    return await verify_reset_code(db, payload.email, payload.verification_code)


@router.post("/reset/with/otp/")
async def _reset_with_otp(payload: ResetOtp, db: AsyncSession = Depends(get_async_db)):
    return await reset_password_with_otp(db, payload.email, payload.otp, payload.new_password)
