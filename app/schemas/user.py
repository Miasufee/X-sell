from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from typing import Optional
from datetime import datetime
from app.models import UserRole


# -------------------------------
# Reusable Field Mixins
# -------------------------------

class EmailSchema(BaseModel):
    email: EmailStr


class UniqueIDSchema(BaseModel):
    unique_id: Optional[str] = None


class RoleSchema(BaseModel):
    role: UserRole = UserRole.USER


class VerificationFlagsSchema(BaseModel):
    is_email_verified: bool = False
    admin_approval: bool = False


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


# -------------------------------
# Password Validation Mixins
# -------------------------------

class PasswordMixin(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)


class ConfirmPasswordMixin(BaseModel):
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if hasattr(self, "password") and self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class NewPasswordMixin(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_new_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match")
        return self


# -------------------------------
# User Schemas
# -------------------------------

class UserBase(EmailSchema, RoleSchema, VerificationFlagsSchema, UniqueIDSchema):
    pass


class UserCreate(UserBase):
    pass


class UserEmailVerification(UserBase):
    verification_code: str


class UserEmail(UserBase):
    pass


class AdminUserCreate(UserBase, PasswordMixin, ConfirmPasswordMixin):
    """Admin user creation schema with password confirmation"""
    pass


class UserCreateInternal(EmailSchema, RoleSchema, VerificationFlagsSchema, UniqueIDSchema):
    """Internal schema for creating users with hashed password"""
    hashed_password: Optional[str] = None


class UserUpdate(EmailSchema, RoleSchema, VerificationFlagsSchema, UniqueIDSchema):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_email_verified: Optional[bool] = None
    admin_approval: Optional[bool] = None


class UserPasswordUpdate(NewPasswordMixin):
    current_password: str


class UserResponse(UserBase, TimestampSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int


# -------------------------------
# Login Schemas
# -------------------------------

class LoginBase(EmailSchema):
    pass


class UserLogin(LoginBase):
    verification_code: Optional[str] = None


class AdminLogin(LoginBase):
    password: str
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

class UserFlagData(EmailSchema):
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

class LoginUserData(EmailSchema, TimestampSchema):
    role: str
    is_email_verified: bool
    admin_approval: bool
    unique_id: str
    id: int


class LoginResponseData(BaseModel):
    access_token: str
    refresh_token: str
    user: LoginUserData


class LoginAPIResponse(BaseModel):
    status_code: int
    detail: str
    data: LoginResponseData


# -------------------------------
# Role & Password Management
# -------------------------------

class RoleUpdateRequest(EmailSchema):
    new_role: UserRole


class ToggleRoleAPIResponse(BaseModel):
    message: str
    data: dict


class PasswordResetPayloadRequest(EmailSchema, UniqueIDSchema):
    unique_id: str


class PasswordResetPayload(EmailSchema, UniqueIDSchema, PasswordMixin):
    verification_code: str
    superuser_secret_key: Optional[str] = None


class EmailVerification(EmailSchema):
    verification_code: Optional[str] = None


class ResetOtp(EmailVerification, PasswordMixin):
    otp: str

# from pydantic import BaseModel, EmailStr, Field, ConfigDict
# from typing import Optional
# from datetime import datetime
#
# from app.models import UserRole
#
#
# # -------------------------------
# # Base User Schemas
# # -------------------------------
#
# class UserBase(BaseModel):
#     email: EmailStr
#     role: UserRole = UserRole.USER
#     is_email_verified: bool = False
#     admin_approval: bool = False
#     unique_id: Optional[str] = None
#
#
# class UserCreate(UserBase):
#     pass
#
#
# class UserEmailVerification(UserBase):
#     verification_code: str
#
#
# class UserEmail(UserBase):
#     pass
#
#
# class AdminUserCreate(UserBase):
#     password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
#     confirm_password: str = Field(..., description="Password confirmation")
#
#     def validate_passwords_match(self):
#         if self.password != self.confirm_password:
#             raise ValueError("Passwords do not match")
#         return self
#
#
# class UserCreateInternal(BaseModel):
#     """Internal schema for creating users with hashed password"""
#     email: EmailStr
#     hashed_password: Optional[str] = None
#     role: UserRole = UserRole.USER
#     is_email_verified: bool = False
#     admin_approval: bool = False
#     unique_id: Optional[str] = None
#
#
# class UserUpdate(BaseModel):
#     email: Optional[EmailStr] = None
#     role: Optional[UserRole] = None
#     is_email_verified: Optional[bool] = None
#     admin_approval: Optional[bool] = None
#     unique_id: Optional[str] = None
#
#
# class UserPasswordUpdate(BaseModel):
#     current_password: str
#     new_password: str = Field(..., min_length=8)
#     confirm_new_password: str
#
#     def validate_passwords_match(self):
#         if self.new_password != self.confirm_new_password:
#             raise ValueError("New passwords do not match")
#         return self
#
#
# class UserResponse(UserBase):
#     model_config = ConfigDict(from_attributes=True)
#
#     id: int
#     created_at: datetime
#     updated_at: datetime
#
#
# # -------------------------------
# # Login Schemas
# # -------------------------------
#
# class LoginBase(BaseModel):
#     email: EmailStr
#
#
# class UserLogin(LoginBase):
#     verification_code: Optional[str] = None
#
#
# class AdminLogin(LoginBase):
#     password: str
#     unique_id: str
#
#
# class SuperUserCreate(AdminLogin):
#     superuser_secret_key: str
#
#
# class SuperUserLogin(AdminLogin):
#     pass
#
# class SuperAdmin(AdminLogin):
#     pass
#
#
# class ApproveRequest(LoginBase):
#     pass
#
#
# # -------------------------------
# # Toggle Flag Response
# # -------------------------------
#
# class UserFlagData(BaseModel):
#     email: EmailStr
#     is_super_admin: Optional[bool] = None
#     admin_approval: Optional[bool] = None
#     is_email_verified: Optional[bool] = None
#
#
# class ToggleInnerResponse(BaseModel):
#     message: str
#     data: UserFlagData
#
#
# class ToggleFlagAPIResponse(BaseModel):
#     status_code: int
#     detail: str
#     data: ToggleInnerResponse
#
#
# # -------------------------------
# # Login Response
# # -------------------------------
#
# class LoginUserData(BaseModel):
#     email: EmailStr
#     role: str
#     is_email_verified: bool
#     admin_approval: bool
#     unique_id: str
#     id: int
#     created_at: datetime
#     updated_at: datetime
#
#
# class LoginResponseData(BaseModel):
#     access_token: str
#     refresh_token: str
#     user: LoginUserData
#
#
# class LoginAPIResponse(BaseModel):
#     status_code: int
#     detail: str
#     data: LoginResponseData
#
# class RoleUpdateRequest(BaseModel):
#     email: EmailStr
#     new_role: UserRole
#
# class ToggleRoleAPIResponse(BaseModel):
#     message: str
#     data: dict
#
# class PasswordResetPayloadRequest(BaseModel):
#     email: EmailStr
#     unique_id: str
#
# class PasswordResetPayload(BaseModel):
#     email: EmailStr
#     verification_code: str
#     new_password: str
#     unique_id: Optional[str] = None
#     superuser_secret_key: Optional[str] = None
#
# class EmailVerification(BaseModel):
#     email: EmailStr
#     verification_code: Optional[str] = None
#
# class ResetOtp(EmailVerification):
#     otp: str
#     new_password: str