from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import SuperUser
from app.schemas.user_schema import (
    SuperUserCreate,
    SuperUserLogin,
    ApproveRequest,
    ToggleFlagAPIResponse,
    LoginAPIResponse,
    RoleUpdateRequest
)
from app.core.auth_service.auth_utils import login, update_role, _get_user_lists
from app.core.auth_service.superuser_service import create_superuser, toggle_flag
import logging
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create")
async def _create_superuser(payload: SuperUserCreate, db: AsyncSession = Depends(get_async_db)):
    return await create_superuser(
        db=db,
        email=payload.email,
        password=payload.hashed_password,
        secret_key=payload.superuser_secret_key
    )

@router.post("/login", response_model=LoginAPIResponse)
async def login_superuser(payload: SuperUserLogin, db: AsyncSession = Depends(get_async_db)):
    return await login(
        db=db,
        email=payload.email,
        password=payload.password,
        unique_id=payload.unique_id
    )

@router.post("/toggle/superadmin/approve", response_model=ToggleFlagAPIResponse)
async def toggle_super_admin_flag(req: ApproveRequest, db: AsyncSession = Depends(get_async_db), actor: SuperUser = None):
    return await toggle_flag(db, actor, req.email, "is_super_admin")

@router.post("/toggle/admin/approve", response_model=ToggleFlagAPIResponse)
async def toggle_admin_flag(req: ApproveRequest, db: AsyncSession = Depends(get_async_db), actor: SuperUser = None):
    return await toggle_flag(db, actor, req.email, "admin_approval")

@router.post("/role/update")
async def _update_role(req: RoleUpdateRequest, db: AsyncSession = Depends(get_async_db), actor: SuperUser = None):
    return await update_role(db, actor, req.email, req.new_role)

@router.get("/users")
async def get_users_lists(db: AsyncSession = Depends(get_async_db), _: SuperUser = None):
    return await _get_user_lists(db)