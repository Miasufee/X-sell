from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import User
from app.core.security import verify_password, create_access_token, create_refresh_token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, user_data: UserCreate) -> User:
        """Register new user"""
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        existing_username = await self.user_repo.get_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user
        user = await self.user_repo.create(user_data)
        
        # TODO: Send email verification
        # await self.send_verification_email(user)
        
        return user

    async def authenticate(self, login_data: UserLogin) -> User:
        """Authenticate user"""
        user = await self.user_repo.get_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        return user

    async def get_current_user(self, user_id: int) -> User:
        """Get current authenticated user"""
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        return user

    def create_tokens(self, user: User) -> dict:
        """Create access and refresh tokens"""
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    async def refresh_access_token(self, user_id: int) -> str:
        """Create new access token from refresh token"""
        user = await self.get_current_user(user_id)
        return create_access_token(data={"sub": str(user.id), "role": user.role.value})

    async def request_password_reset(self, email: str) -> None:
        """Request password reset"""
        user = await self.user_repo.get_by_email(email)
        
        if user:
            # TODO: Send password reset email
            # reset_token = create_password_reset_token(user.id)
            # await self.send_password_reset_email(user, reset_token)
            pass

    async def verify_email(self, user_id: int) -> User:
        """Verify user email"""
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return await self.user_repo.verify_email(user)
