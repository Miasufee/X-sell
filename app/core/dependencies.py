from typing import Annotated, TypeAlias
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.models import User, UserRole


def get_security_manager():
    from app.core.security import security_manager
    return security_manager


# ---- Dependency functions (properly structured for FastAPI) ----
async def _current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> User:
    return await get_security_manager().get_current_user(request=request, db=db)

async def _admin_user(
    current_user: User = Depends(_current_user)
) -> User:
    security_manager = get_security_manager()
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SUPERUSER]:
        from app.core.utils.response.exceptions import Exceptions
        raise Exceptions.permission_denied()
    return current_user

async def _super_admin_user(
    current_user: User = Depends(_current_user)
) -> User:
    if current_user.role not in [UserRole.SUPER_ADMIN]:
        from app.core.utils.response.exceptions import Exceptions
        raise Exceptions.permission_denied()
    return current_user

async def _super_user(
    current_user: User = Depends(_current_user)
) -> User:
    if current_user.role not in [UserRole.SUPERUSER]:
        from app.core.utils.response.exceptions import Exceptions
        raise Exceptions.permission_denied()
    return current_user


# ---- Annotated aliases ----
CurrentUser: TypeAlias = Annotated[User, Depends(_current_user)]
AdminUser: TypeAlias = Annotated[User, Depends(_admin_user)]
SuperAdminUser: TypeAlias = Annotated[User, Depends(_super_admin_user)]
SuperUser: TypeAlias = Annotated[User, Depends(_super_user)]
