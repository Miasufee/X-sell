from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils.generate import VerificationManager
from app.core.utils.response.exceptions import Exceptions
from app.core.utils.response.success import Success
from app.core.utils.token_manager import token_manager
from app.crud import user_crud
from app.schemas import UserResponse


async def create_user(db: AsyncSession, email):
    existing_user = await user_crud.get_user_by_email(db=db, email=email)
    if existing_user:
        raise Exceptions.email_exist(detail="Email exist please login to continue")
    new_user = await user_crud.create(db=db, email=email)
    user_response = UserResponse.model_validate(new_user)
    return Success.account_created(user=user_response)


async def login_user(db: AsyncSession, email, verification_code: Optional[str] = None):
    db_user = await user_crud.get_user_by_email(db=db, email=email)
    if not db_user:
        raise Exceptions.email_not_registered()
    if not db_user.is_verify:
        raise Exceptions.not_verified()
    if verification_code:
        if not await VerificationManager.verify_code(
                user_id=db_user.id,
                code=verification_code,
                db=db
        ):
            raise Exceptions.invalid_verification_code()
        tokens, _ = await token_manager.create_tokens(db, db_user)
        return Success.login_success(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            user=UserResponse.model_validate(db_user),
        )
    verification_code = await VerificationManager.generate_code(user_id=db_user.id, db=db)
    return Success.verification_code_sent(verification_code=verification_code)