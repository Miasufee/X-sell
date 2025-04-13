from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import secrets
from datetime import datetime, timedelta

from app.database import get_async_db
from app.crud import verification_code_crud


async def generate_verification_code(user_id: int, db: AsyncSession = Depends(get_async_db)):
    async with db:
        code = ''.join(secrets.choice('1234567890') for _ in range(6))
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        existing_code = verification_code_crud.get_verification_code(db, user_id)
        if existing_code:
            existing_code.code = code
            existing_code.expires_at = expires_at
        else:
            await verification_code_crud.create(db, user_id, code, expires_at)

        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            await verification_code_crud.delete_verification_code(db, user_id)
            await verification_code_crud.create(db, user_id, code, expires_at)
            await db.commit()
    return code
