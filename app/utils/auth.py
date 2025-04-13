

import secrets
from passlib.context import CryptContext
import pytz
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timedelta
from app.models import User, UserRole
from app.config import settings
from app.crud import refresh_token_crud, user_crud
from app.database import get_async_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await user_crud.get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user


def get_user_with_permission(role: UserRole):
    async def _get_user_with_permission(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have {role.value} privileges."
            )
        return current_user
    return _get_user_with_permission


def get_user_with_any_role(allowed_roles: List[UserRole]):
    async def _get_user_with_any_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have the required privileges. Allowed roles: "
                       f"{', '.join([role.value for role in allowed_roles])}"
            )
        return current_user
    return _get_user_with_any_role


get_superuser = get_user_with_permission(UserRole.SUPERUSER)
get_admin = get_user_with_permission(UserRole.ADMIN)
get_admin_or_superuser = get_user_with_any_role([UserRole.ADMIN, UserRole.SUPERUSER])
get_user_or_above = get_user_with_any_role([UserRole.USER, UserRole.ADMIN, UserRole.SUPERUSER])


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, settings.ALGORITHM)


async def create_refresh_token(user_id: int, db: AsyncSession = Depends(get_async_db)):
    expires_at = datetime.now(pytz.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token = secrets.token_urlsafe(32)
    db_token = await refresh_token_crud.create(db=db, user_id=user_id, token=token, expires_at=expires_at)
    return {"token": db_token.token, "expires_at": db_token.expires_at}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hashed_the_password(plain_password: str):
    return pwd_context.hash(plain_password)
