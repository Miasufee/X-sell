from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import security_manager
from app.core.utils.generate import IDGenerator, IDPrefix
from app.core.utils.response.exceptions import Exceptions
from app.core.utils.response.success import Success
from app.crud import user_crud
from app.models import User, UserRole


async def create_superuser(
        db: AsyncSession,
        email,
        password: str,
        secret_key: str
) -> User:
    """Create the one and only SUPERUSER with secret key check"""
    if secret_key != settings.API_SUPERUSER_SECRET_KEY:
        raise Exceptions.forbidden()

    existing = await user_crud.get(db, role=UserRole.SUPERUSER)
    if existing:
        raise Exceptions.forbidden("Superuser already exists")

    hashed_pw = security_manager.hash_password(password)
    unique_id = IDGenerator.generate_id(IDPrefix.SUPERUSER, total_length=12)

    return await user_crud.create(
        db,
        email=email,
        role=UserRole.SUPERUSER,
        hashed_password=hashed_pw,
        unique_id=unique_id
    )


async def toggle_flag(db: AsyncSession, actor: User, target_email, flag: str):
    db_user = await user_crud.get(db=db, email=target_email)
    if not db_user:
        raise Exceptions.not_found("User not found")

    # RULES
    if actor.role == UserRole.SUPERUSER:
        pass  # full control
    elif actor.role == UserRole.SUPER_ADMIN:
        # Only allow `admin_approval` flag on USER/ADMIN targets
        if flag != "admin_approval":
            raise Exceptions.forbidden("SUPER_ADMIN can only toggle admin_approval")
        if db_user.role not in [UserRole.USER, UserRole.ADMIN]:
            raise Exceptions.forbidden("SUPER_ADMIN can only toggle flags for USER/ADMIN")
    else:
        raise Exceptions.forbidden("Only SUPERUSER or SUPER_ADMIN can toggle flags")

    # Safety check for flag existence
    if not hasattr(db_user, flag) or not isinstance(getattr(db_user, flag), bool):
        raise Exceptions.bad_request(f"Invalid boolean flag '{flag}'")

    # Flip the flag
    setattr(db_user, flag, not getattr(db_user, flag))
    await db.commit()
    await db.refresh(db_user)

    return Success.ok(
        message=f"{flag.replace('_', ' ').title()} status updated",
        data={"email": db_user.email, flag: getattr(db_user, flag)},
    )

async def update_role(db: AsyncSession, actor: User, target_email: str, new_role: UserRole):
    db_user = await user_crud.get(db=db, email=target_email)
    if not db_user:
        raise Exceptions.not_found("User not found")
    if not isinstance(new_role, UserRole):
        raise Exceptions.bad_request("Invalid role")

    # RULES
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

    # --- Role transition logic ---
    if new_role == UserRole.ADMIN:
        db_user.role, db_user.unique_id = UserRole.ADMIN, IDGenerator.generate_id(IDPrefix.ADMIN, 12)
    elif new_role == UserRole.SUPER_ADMIN:
        db_user.role, db_user.unique_id = UserRole.SUPER_ADMIN, IDGenerator.generate_id(IDPrefix.SUPER_ADMIN, 12)
    elif new_role == UserRole.USER:
        if db_user.role == UserRole.USER:
            raise Exceptions.forbidden("User already has USER role")
        db_user.role, db_user.unique_id = UserRole.USER, None

    await db.commit()
    await db.refresh(db_user)
