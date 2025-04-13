from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    pass


class UserLogin(UserBase):
    verification_code: Optional[str] = None


class VerifyUser(UserLogin):
    pass
