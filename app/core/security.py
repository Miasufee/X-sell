from fastapi import Request, Depends
from jose import jwt, JWTError
from passlib.context import CryptContext
import hmac
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings
from app.core.database import get_async_db
from app.core.utils.response.exceptions import Exceptions
from app.crud.user_crud import user_crud

from app.models import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

class SecurityManager:
    """Handles authentication, password hashing, and role-based authorization."""

    # ----- PASSWORD -----
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def constant_time_compare(val1: str, val2: str) -> bool:
        return hmac.compare_digest(str(val1), str(val2))

    # ----- TOKEN -----
    @staticmethod
    async def get_token(request: Request) -> str:
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")

        if not token:
            raise Exceptions.credentials_exception()

        return token

    # ----- CURRENT USER -----
    @staticmethod
    async def get_current_user(
            request: Request = None,
            db: AsyncSession = None,
            token: str = None
    ) -> User:
        """
        Works both:
        - As a FastAPI dependency: request/db automatically injected
        - As a manual call: pass request & db explicitly
        """
        if token is None:
            if request is None:
                raise ValueError("Request object required when token is not provided")
            token = await SecurityManager.get_token(request)

        if db is None:
            raise ValueError("Database session is required")

        try:

            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id_raw = payload.get("sub")
            if user_id_raw is None:
                print("No user ID found in JWT payload")
                raise Exceptions.credentials_exception()

            # Convert to integer for database lookup (handles both string and int)
            try:
                user_id = int(user_id_raw)
            except (ValueError, TypeError):
                raise Exceptions.credentials_exception()

            token_version: int = payload.get("version", 0)

            user = await user_crud.get_user_by_id(db, user_id)
            if user is None:
                raise Exceptions.credentials_exception()

            if user.token_version != token_version:
                raise Exceptions.credentials_exception()

            return user

        except JWTError as e:
            logger.error(f"Unexpected error during : {e}")
            raise Exceptions.credentials_exception()
        except Exception as e:
            logger.error(f"Unexpected error during : {e}")
            raise Exceptions.credentials_exception()

    # Dependency wrapper for FastAPI
    def current_user_dep(self):
        async def _dep(
                request: Request,
                db: AsyncSession = Depends(get_async_db)
        ) -> User:
            return await self.get_current_user(request=request, db=db)

        return Depends(_dep)

    # ----- ROLE CHECKS -----
    def require_role_dep(self, allowed_roles: list[UserRole]):
        async def _dep(
                current_user: User = Depends(self.current_user_dep())
        ) -> User:
            if current_user.role not in allowed_roles:
                raise Exceptions.permission_denied()
            return current_user

        return Depends(_dep)

    # ----- TOKEN CREATION -----
    @staticmethod
    def create_access_token(user_id: int, token_version: int = 1) -> str:
        """Create a properly formatted JWT access token with string subject."""
        import time

        payload = {
            "sub": str(user_id),
            "exp": int(time.time()) + (settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            "jti": SecurityManager._generate_jti(),
            "version": token_version
        }

        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token

    @staticmethod
    def create_refresh_token(user_id: int, token_version: int = 1) -> str:
        """Create a properly formatted JWT refresh token with string subject."""
        import time

        payload = {
            "sub": str(user_id),
            "exp": int(time.time()) + (settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
            "jti": SecurityManager._generate_jti(),
            "version": token_version
        }

        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token

    @staticmethod
    def _generate_jti() -> str:
        """Generate a unique JWT ID."""
        import secrets
        import string
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))


security_manager = SecurityManager()
