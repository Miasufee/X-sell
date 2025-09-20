from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Index, UniqueConstraint, Float
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base, IntIdMixin, TimeStampMixin


class UserRole(PyEnum):
    USER = "user"
    MERCHANT = "merchant"
    ADMIN = "admin"
    SUPER_ADMIN = "SuperAdmin"
    SUPERUSER = "Superuser"


class SocialProvider(PyEnum):
    google = "Google"
    icloud = "iCloud"

class User(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    admin_approval = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    is_super_admin = Column(Boolean, default=False, nullable=False)
    unique_id = Column(String(15), nullable=True, unique=True)
    token_version = Column(Integer, default=1, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)


    # Relationships
    shops = relationship("Shop", back_populates="merchant")
    products = relationship("Product", back_populates="merchant")
    cart = relationship("Cart", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    merchant_application = relationship("MerchantApplication", foreign_keys="MerchantApplication.user_id",
                                        back_populates="user", uselist=False)
    profile = relationship("UserProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete-orphan")
    phone_numbers = relationship("PhoneNumber", back_populates="user", cascade="all, delete-orphan")
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    verification_codes = relationship("VerificationCode", back_populates="user", cascade="all, delete-orphan")
    refreshed_tokens = relationship("RefreshedToken", back_populates="user", cascade="all, delete-orphan")
    locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "user_profile"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar_url = Column(String(512), nullable=True)

    user = relationship("User", back_populates="profile")


class PhoneNumber(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "phone_number"
    __table_args__ = (Index("idx_phone_number", "country_code", "phone_number", unique=True),)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    country_code = Column(String(4), nullable=False)
    phone_number = Column(String(20), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="phone_numbers")


class Address(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "address"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    region = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    street = Column(String(255), nullable=False)
    street2 = Column(String(255), nullable=True)
    house_number = Column(String(20), nullable=False)

    user = relationship("User", back_populates="addresses")


class SocialAccount(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "social_account"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(SocialProvider), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    access_token = Column(String(512), nullable=False)

    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)

    user = relationship("User", back_populates="social_accounts")


class VerificationCode(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "verification_code"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="verification_codes")


class RefreshedToken(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "refreshed_token"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    refresh_token = Column(String(510), nullable=False)
    expires_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="refreshed_tokens")

class UserLocation(Base, IntIdMixin, TimeStampMixin):
    __tablename__ = "user_location"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    user = relationship("User", back_populates="locations")
