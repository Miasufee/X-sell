from fastapi import APIRouter

from app.routes.auth import user, superuser, utils, super_admin
from app.routes.endpoints import merchant_routes

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(user.router, prefix="/user/auth", tags=["authentication"])
api_router.include_router(superuser.router, prefix="/superuser/auth", tags=["authentication"])
api_router.include_router(utils.router, prefix="/auth/utils", tags=["authentication"])
api_router.include_router(super_admin.router, prefix="/admin/auth", tags=["authentication"])
api_router.include_router(merchant_routes.router, prefix="/merchant", tags=["merchant"])