import secrets
import string
import time
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from jose import jwt, JWTError
from pydantic import BaseModel

from app.core.config import settings
from app.crud.user_management.verification_code_crud import verification_code_crud


class IDPrefix(Enum):
    """Prefixes for different ID types"""
    VIDEO = "VI"
    LIVE_STREAM = "LS"
    USER = "US"
    SUPERUSER = "SU"
    SUPER_ADMIN = "SA"
    ADMIN = "AD"


class IDGenerator:
    # Base62 character set (0-9, A-Z, a-z)
    BASE62 = string.digits + string.ascii_letters

    @classmethod
    def base62_encode(cls, number: int) -> str:
        """Encode number to base62 string"""
        if number == 0:
            return cls.BASE62[0]

        encoded = []
        while number > 0:
            number, remainder = divmod(number, 62)
            encoded.append(cls.BASE62[remainder])
        return ''.join(reversed(encoded))

    @classmethod
    def generate_timestamp_component(cls) -> str:
        """Generate timestamp component (millisecond precision)"""
        return cls.base62_encode(int(time.time() * 1000))

    @classmethod
    def generate_random_component(cls, length: int) -> str:
        """Generate cryptographically secure random component"""
        return ''.join(secrets.choice(cls.BASE62) for _ in range(length))

    @classmethod
    def generate_id(cls, prefix: IDPrefix, total_length: int = 12) -> str:
        """
        Generate a unique ID with:
        - Prefix (2 chars)
        - Timestamp (variable)
        - Random component (remaining)
        """
        if total_length < 8:
            raise ValueError("ID length must be at least 8 characters")

        prefix_part = prefix.value
        timestamp_part = cls.generate_timestamp_component()
        remaining_length = total_length - len(prefix_part)

        # Ensure minimum randomness
        min_random = 4
        if len(timestamp_part) > remaining_length - min_random:
            timestamp_part = timestamp_part[:remaining_length - min_random]

        random_part = cls.generate_random_component(remaining_length - len(timestamp_part))
        return f"{prefix_part}{timestamp_part}{random_part}"


class VerificationManager:
    @staticmethod
    async def generate_code(
            user_id: int,
            db: AsyncSession,
            code_length: int = 6,
            expiry_minutes: int = 10,
            max_retries: int = 3
    ) -> str:
        """Generate and store verification code"""
        for attempt in range(max_retries):
            try:
                code = ''.join(secrets.choice(string.digits) for _ in range(code_length))
                expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

                # Upsert pattern
                existing = await verification_code_crud.get_verification_code(db, user_id)
                if existing:
                    existing.code = code
                    existing.expires_at = expires_at
                    db.add(existing)
                else:
                    await verification_code_crud.create_verification_code(
                        db=db,
                        user_id=user_id,
                        code=code,
                        expires_at=expires_at
                    )

                await db.commit()
                return code
            except IntegrityError:
                await db.rollback()
                if attempt == max_retries - 1:
                    raise ValueError("Failed to generate unique verification code")
                continue

    @staticmethod
    async def verify_code(
            user_id: int,
            code: str,
            db: AsyncSession
    ) -> bool:
        """Verify and consume a verification code"""
        valid_code = await verification_code_crud.get_valid_code(db, user_id, code)
        if valid_code:
            await verification_code_crud.delete_code(db, user_id, code)
            await db.commit()
            return True
        return False


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int  # user_id
    exp: int  # expiration timestamp
    jti: str  # token unique identifier
    version: int  # token version


class TokenGenerator:
    def __init__(self):
        self.access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expires = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    @staticmethod
    def generate_jti() -> str:
        """Generate a unique JWT ID"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

    def create_token_pair(
            self,
            user_id: int,
            token_version: int = 1
    ) -> Tuple[Token, datetime]:
        """
        Generate both access and refresh tokens

        Args:
            user_id: int - user identifier
            token_version: int - current token version

        Returns:
            Tuple[Token, datetime]: Token pair and refresh token expiration
        """
        # Generate unique IDs for both tokens
        access_jti = self.generate_jti()
        refresh_jti = self.generate_jti()

        # Calculate expiration times
        access_expires = datetime.now(timezone.utc) + self.access_token_expires
        refresh_expires = datetime.now(timezone.utc) + self.refresh_token_expires

        # Create access token payload
        access_payload = TokenPayload(
            sub=user_id,
            exp=int(access_expires.timestamp()),
            jti=access_jti,
            version=token_version
        ).dict()

        # Create refresh token payload
        refresh_payload = TokenPayload(
            sub=user_id,
            exp=int(refresh_expires.timestamp()),
            jti=refresh_jti,
            version=token_version
        ).dict()

        # Generate tokens
        access_token = jwt.encode(
            access_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        refresh_token = jwt.encode(
            refresh_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        return Token(access_token=access_token, refresh_token=refresh_token), refresh_expires

    def verify_access_token(
            self,
            token: str
    ) -> Optional[TokenPayload]:
        """
        Verify an access token and return its payload

        Args:
            token: str - JWT access token

        Returns:
            Optional[TokenPayload]: Decoded token payload if valid
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return TokenPayload(**payload)
        except (JWTError, ValueError):
            return None


# Initialize token generator
token_generator = TokenGenerator()