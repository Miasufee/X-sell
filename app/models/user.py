from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from .base import Base, IdMixin, TimeStampMixin


class UserRole(enum.Enum):
    USER = "user"
    SELLER = "seller"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class User(Base, IdMixin, TimeStampMixin):
    """Model for managing users."""
    __tablename__ = "users"

    email = Column(String(225), unique=True, index=True, nullable=False)
    user_role = Column(Enum(UserRole, name="user role"), default=UserRole.USER, nullable=False)
    is_verified = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)

    # Fields only for admin and superuser
    unique_id = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)

    verification_codes = relationship("VerificationCode", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class VerificationCode(Base, IdMixin, TimeStampMixin):
    """Model for managing user verification code."""
    __tablename__ = "verification_codes"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="verification_codes")


class RefreshToken(Base, IdMixin, TimeStampMixin):
    """Model for managing user refresh tokens."""
    __tablename__ = "refresh_tokens"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    # relationship
    user = relationship("User", back_populates="refresh_tokens")
