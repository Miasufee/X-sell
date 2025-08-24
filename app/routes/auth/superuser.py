from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import SuperUser
from app.schemas.user import (
    SuperUserCreate,
    SuperUserLogin,
    ApproveRequest,
    ToggleFlagAPIResponse,
    LoginAPIResponse,
    RoleUpdateRequest,
    ToggleRoleAPIResponse
)
from app.services.auth.auth_utils import login
from app.services.auth.superuser_service import create_superuser, toggle_flag

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
        db=db, email=payload.email, password=payload.hashed_password,
        unique_id=payload.unique_id
    )

@router.post("/toggle/superadmin/approve", response_model=ToggleFlagAPIResponse)
async def toggle_super_admin_flag(req: ApproveRequest, db: AsyncSession = Depends(get_async_db), actor: SuperUser = None):
    return await toggle_flag(db, actor, req.email, "is_super_admin")

@router.post("/toggle/admin/approve", response_model=ToggleFlagAPIResponse)
async def toggle_admin_flag(req: ApproveRequest, db: AsyncSession = Depends(get_async_db), actor: SuperUser = None):
    return await toggle_flag(db, actor, req.email, "admin_approval")

@router.post("/role/update", response_model=ToggleRoleAPIResponse)
async def update_role(req: RoleUpdateRequest, db: AsyncSession = Depends(get_async_db), actor: SuperUser = None):
    return await update_role(db, actor, req.email, req.new_role)
