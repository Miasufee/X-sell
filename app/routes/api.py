from fastapi import APIRouter

from app.routes.auth import user, superuser

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(user.router, prefix="/user/auth", tags=["authentication"])
api_router.include_router(superuser.router, prefix="/superuser/auth", tags=["authentication"])
