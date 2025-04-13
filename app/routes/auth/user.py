from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.crud import user_crud, verification_code_crud
from app.schemas import UserCreate, UserLogin, VerifyUser
from app.utils.responses.exceptions import Exceptions
from app.utils.responses.success import Success
from app.utils.generate import generate_verification_code
from app.utils.auth import create_access_token
from app.utils.messages.mails import send_verification_code

router = APIRouter()


@router.post('/create/user/')
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    existing_user = await user_crud.get_user_by_email(db, user_data.email)
    if existing_user:
        Exceptions.email_exist()
    new_user = await user_crud.create(db, **user_data.dict())
    verification_code = await generate_verification_code(new_user.id, db)
    await send_verification_code(verification_code)
    return Success.account_created(new_user)


@router.post("/verify/user", status_code=status.HTTP_200_OK, response_model=dict)
async def verify_email(user: VerifyUser, db: AsyncSession = Depends(get_async_db)):
    db_user = await user_crud.get_user_by_email(db, email=user.email)
    if not db_user:
        Exceptions.email_not_registered()
    if db_user.is_verified:
        Exceptions.not_verify()
    if await verification_code_crud.verify_code(db, db_user.id, user.verification_code):
        db_user.is_verified = True
        await db.commit()
        return Success.ok()
    else:
        Exceptions.invalid_verification_code()


@router.post('/login/user/')
async def login_user(user_data: UserLogin, response: Response, db: AsyncSession = Depends(get_async_db)):
    db_user = await user_crud.get_user_by_email(db, user_data.email)

    if not db_user:
        Exceptions.email_not_registered()
    if not db_user.is_verified:
        Exceptions.not_verify()

    if user_data.verification_code:
        if await verification_code_crud.verify_code(db, db_user.id, user_data.verification_code):
            access_token = await create_access_token({"sub": db_user.email})

            # Set HTTP-only cookie
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="strict"
            )
            return Success.ok()
        else:
            Exceptions.invalid_verification_code()
    else:
        verification_code = await generate_verification_code(db_user.id, db)
        await send_verification_code(verification_code)
        return Success.ok()


@router.get('/verification/code')
async def get_new_verification_code(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    db_user = await user_crud.get_user_by_email(db, user_data.email)
    if not db_user:
        Exceptions.email_not_registered()
    verification_code = await generate_verification_code(db_user.id, db)
    return Success.verification_code_sent(verification_code)
