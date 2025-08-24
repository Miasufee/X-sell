from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

from app.models import UserRole


# -------------------------------
# Base User Schemas
# -------------------------------

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.USER
    is_email_verified: bool = False
    admin_approval: bool = False
    unique_id: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserEmailVerification(UserBase):
    verification_code: str


class UserEmail(UserBase):
    pass


class AdminUserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    confirm_password: str = Field(..., description="Password confirmation")

    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserCreateInternal(BaseModel):
    """Internal schema for creating users with hashed password"""
    email: EmailStr
    hashed_password: Optional[str] = None
    role: UserRole = UserRole.USER
    is_email_verified: bool = False
    admin_approval: bool = False
    unique_id: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_email_verified: Optional[bool] = None
    admin_approval: Optional[bool] = None
    unique_id: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str

    def validate_passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match")
        return self


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# -------------------------------
# Login Schemas
# -------------------------------

class LoginBase(BaseModel):
    email: EmailStr


class UserLogin(LoginBase):
    verification_code: Optional[str] = None


class AdminLogin(LoginBase):
    hashed_password: str
    unique_id: str


class SuperUserCreate(AdminLogin):
    superuser_secret_key: str


class SuperUserLogin(AdminLogin):
    pass

class SuperAdmin(AdminLogin):
    pass


class ApproveRequest(LoginBase):
    pass


# -------------------------------
# Toggle Flag Response
# -------------------------------

class UserFlagData(BaseModel):
    email: EmailStr
    is_super_admin: Optional[bool] = None
    admin_approval: Optional[bool] = None
    is_email_verified: Optional[bool] = None


class ToggleInnerResponse(BaseModel):
    message: str
    data: UserFlagData


class ToggleFlagAPIResponse(BaseModel):
    status_code: int
    detail: str
    data: ToggleInnerResponse


# -------------------------------
# Login Response
# -------------------------------

class LoginUserData(BaseModel):
    email: EmailStr
    role: str
    is_email_verified: bool
    admin_approval: bool
    unique_id: str
    id: int
    created_at: datetime
    updated_at: datetime


class LoginResponseData(BaseModel):
    access_token: str
    refresh_token: str
    user: LoginUserData


class LoginAPIResponse(BaseModel):
    status_code: int
    detail: str
    data: LoginResponseData

class RoleUpdateRequest(BaseModel):
    email: EmailStr
    new_role: UserRole

class ToggleRoleAPIResponse(BaseModel):
    message: str
    data: dict
    

class PasswordResetPayload(BaseModel):
    email: EmailStr
    verification_code: str
    new_password: str
    unique_id: Optional[str] = None
    superuser_secret_key: Optional[str] = None
