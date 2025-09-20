import asyncio
import random
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import security_manager
from app.core.utils.generate import VerificationManager, IDGenerator, IDPrefix
from app.core.utils.response.exceptions import Exceptions
from app.core.utils.response.success import Success
from app.core.utils.token_manager import token_manager
from app.crud import user_crud
from app.models import UserRole, User
from app.schemas import UserResponse


# -------------------- LOGIN --------------------
import logging
logger = logging.getLogger(__name__)

async def login(db: AsyncSession, email, password: str, unique_id: str):
    """
    Authenticate user with email, password, and unique_id.
    - Performs constant-time check to prevent timing attacks.
    - Verifies account status and role restrictions.
    """
    if not email or not password or not unique_id:
        raise Exceptions.invalid_credentials()

    await asyncio.sleep(random.uniform(0.05, 0.15))  # constant-time check

    db_user = await user_crud.get_user_by_email(db=db, email=email)

    # Placeholders for timing attack resistance
    fake_hash = security_manager.hash_password("fake_password")
    fake_unique_id = "fake_unique_id_12345"

    hashed_password_to_check = db_user.hashed_password if db_user else fake_hash
    unique_id_to_check = db_user.unique_id if db_user else fake_unique_id

    password_ok = security_manager.verify_password(password, hashed_password_to_check)
    unique_id_ok = unique_id == unique_id_to_check

    if not (db_user and password_ok and unique_id_ok):
        raise Exceptions.invalid_credentials()

    # --- DB conditions ---
    if not db_user.is_verified:
        raise Exceptions.forbidden("Email not verified")

    if not db_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SUPERUSER]:
        raise Exceptions.forbidden("Admin approval required")

    tokens, _ = await token_manager.create_tokens(db, db_user)

    return Success.login_success(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user=UserResponse.model_validate(db_user),
    )



# -------------------- EMAIL VERIFICATION --------------------
async def get_verification_code(db: AsyncSession, email):
    """
    Generate and send a verification code to the user’s email.
    """
    db_user = await user_crud.get_user_by_email(db, email)
    if not db_user:
        raise Exceptions.email_not_registered()

    verification_code = await VerificationManager.generate_code(user_id=db_user.id, db=db)
    return Success.verification_code_sent(verification_code)


async def verify_email(db: AsyncSession, email, verification_code: str):
    """
    Verify the user’s email with the provided verification code.
    """
    db_user = await user_crud.get_user_by_email(db, email=email)
    if not db_user:
        raise Exceptions.email_not_registered()

    if not await VerificationManager.verify_code(user_id=db_user.id, code=verification_code, db=db):
        raise Exceptions.invalid_verification_code()

    db_user.is_verified = True
    await db.commit()
    return Success.email_verified()


# -------------------- ROLE MANAGEMENT --------------------
async def update_role(db: AsyncSession, actor: User, target_email, new_role: UserRole):
    """
    Update the role of a user.
    - Only SUPERUSER and SUPER_ADMIN can modify roles.
    - Prevents downgrading SUPERUSER role.
    """
    db_user = await user_crud.get(db=db, email=target_email)
    if not db_user:
        raise Exceptions.not_found("User not found")
    if not isinstance(new_role, UserRole):
        raise Exceptions.bad_request("Invalid role")

    # Role rules
    if actor.role == UserRole.SUPERUSER:
        pass  # full control
    elif actor.role == UserRole.SUPER_ADMIN:
        if db_user.role not in [UserRole.USER, UserRole.ADMIN] or new_role not in [UserRole.USER, UserRole.ADMIN]:
            raise Exceptions.forbidden("SUPER_ADMIN can only toggle USER ↔ ADMIN")
    else:
        raise Exceptions.forbidden("Only SUPERUSER or SUPER_ADMIN can change roles")

    # 🚫 Prevent downgrading SUPERUSER
    if db_user.role == UserRole.SUPERUSER and new_role != UserRole.SUPERUSER:
        raise Exceptions.forbidden("Cannot change role of SUPERUSER")
    if db_user.role == new_role:
        raise Exceptions.already_verified(detail="already upgrade role")
    # --- Role transition logic ---
    if new_role == UserRole.ADMIN:
        db_user.role = UserRole.ADMIN
        db_user.unique_id = IDGenerator.generate_id(IDPrefix.ADMIN, 12)
    elif new_role == UserRole.SUPER_ADMIN:
        db_user.role = UserRole.SUPER_ADMIN
        db_user.unique_id = IDGenerator.generate_id(IDPrefix.SUPER_ADMIN, 12)
    elif new_role == UserRole.USER:
        if db_user.role == UserRole.USER:
            raise Exceptions.forbidden("User already has USER role")
        db_user.role = UserRole.USER
        db_user.unique_id = None

    await db.commit()
    await db.refresh(db_user)
    return Success.ok(detail="User role update success")


# -------------------- PASSWORD RESET --------------------
async def request_password_reset(
    db: AsyncSession,
    email,
    unique_id: str | None = None,
    superuser_secret_key: str | None = None,
):
    """
    Step 1: Request password reset.
    - Superuser → requires email, unique_id, and superuser_secret_key.
    - Admin/SuperAdmin → requires email and unique_id.
    - Normal users are not allowed.
    """
    db_user = await user_crud.get_user_by_email(db, email)
    if not db_user:
        raise Exceptions.email_not_registered()
    if not db_user.is_verified:
        raise Exceptions.forbidden("Email not verified")
    if db_user.role not in [UserRole.SUPERUSER, UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise Exceptions.forbidden("Only ADMIN, SUPER_ADMIN, and SUPERUSER can use this reset flow")

    # Role-specific checks
    if db_user.role == UserRole.SUPERUSER:
        if not (superuser_secret_key and unique_id):
            raise Exceptions.forbidden("Superuser requires secret key and unique_id")
        if superuser_secret_key != settings.API_SUPERUSER_SECRET_KEY:
            raise Exceptions.forbidden("Invalid superuser secret key")
        if unique_id != db_user.unique_id:
            raise Exceptions.invalid_credentials("Invalid unique_id")

    elif db_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if not unique_id:
            raise Exceptions.forbidden("Admin/Superadmin requires unique_id")
        if unique_id != db_user.unique_id:
            raise Exceptions.invalid_credentials("Invalid unique_id")

    verification_code = await VerificationManager.generate_code(user_id=db_user.id, db=db)
    return Success.verification_code_sent(verification_code)


async def verify_reset_code(db: AsyncSession, email, verification_code: str):
    """
    Step 2: Verify reset code.
    - If verified → generate a temporary OTP unique_id.
    """
    db_user = await user_crud.get_user_by_email(db, email=email)
    if not db_user:
        raise Exceptions.email_not_registered()

    if not await VerificationManager.verify_code(user_id=db_user.id, code=verification_code, db=db):
        raise Exceptions.invalid_verification_code()

    # Generate temporary unique_id (OTP)
    if db_user.role == UserRole.SUPERUSER:
        db_user.unique_id = IDGenerator.generate_id(IDPrefix.SUPERUSER, 12)
    elif db_user.role == UserRole.SUPER_ADMIN:
        db_user.unique_id = IDGenerator.generate_id(IDPrefix.SUPER_ADMIN, 12)
    elif db_user.role == UserRole.ADMIN:
        db_user.unique_id = IDGenerator.generate_id(IDPrefix.ADMIN, 12)

    await db.commit()
    await db.refresh(db_user)

    return Success.ok(
        message="Verification successful, use new unique_id as OTP to reset password",
        data={"email": db_user.email, "unique_id": db_user.unique_id},
    )


async def reset_password_with_otp(
    db: AsyncSession,
    email,
    otp_unique_id: str,
    new_password: str
):
    """
    Step 3: Final password reset.
    - Requires email + OTP (unique_id) + new password.
    - Invalidates OTP after use by rotating unique_id.
    """
    db_user = await user_crud.get_user_by_email(db, email=email)
    if not db_user:
        raise Exceptions.email_not_registered()

    if otp_unique_id != db_user.unique_id:
        raise Exceptions.invalid_credentials("Invalid OTP unique_id")

    # Save new password
    db_user.hashed_password = security_manager.hash_password(new_password)

    # Rotate unique_id again (invalidate OTP after use)
    if db_user.role == UserRole.SUPERUSER:
        db_user.unique_id = IDGenerator.generate_id(IDPrefix.SUPERUSER, 12)
    elif db_user.role == UserRole.SUPER_ADMIN:
        db_user.unique_id = IDGenerator.generate_id(IDPrefix.SUPER_ADMIN, 12)
    elif db_user.role == UserRole.ADMIN:
        db_user.unique_id = IDGenerator.generate_id(IDPrefix.ADMIN, 12)

    await db.commit()
    await db.refresh(db_user)

    return Success.ok(
        message="Password reset successfully",
        data={"email": db_user.email, "role": db_user.role.value},
    )

async def _get_user_lists(db: AsyncSession):
    return await user_crud.get_users(db)