from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_async_db
from app.core.utils.response.exceptions import Exceptions
from app.schemas import (
    MerchantApplicationCreate,
    MerchantApplicationResponse,
    MerchantApplicationStatusUpdate,
    MerchantApplicationStats,
    MerchantApplicationSearch,
    PaginatedResponse
)
from app.crud.merchant_crud import  merchant_crud
from app.core.dependencies import AdminUser, RegularUser

router = APIRouter()


@router.post("/", response_model=MerchantApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant_application(
        application_data: MerchantApplicationCreate,
        db: AsyncSession = Depends(get_async_db),
        user: RegularUser = None
):
    """Create a new merchant application."""
    return await merchant_crud.create_application(db, user.id, **application_data.model_dump())


@router.get("/my-application", response_model=Optional[MerchantApplicationResponse])
async def get_my_application(
        db: AsyncSession = Depends(get_async_db),
        user: RegularUser = None
):
    """Get current user's merchant application."""
    return await merchant_crud.get_user_application(db, user.id)


@router.get("/get-applications", response_model=PaginatedResponse[MerchantApplicationResponse])
async def get_applications(
        search_params: MerchantApplicationSearch = Depends(),
        db: AsyncSession = Depends(get_async_db),
        _: AdminUser = None
):
    """Get merchant applications with search and pagination (Admin only)."""
    skip = (search_params.page - 1) * search_params.per_page

    applications = await merchant_crud.search_applications(
        db,
        search_term=search_params.search_term,
        status=search_params.status,
        min_date=search_params.min_date,
        max_date=search_params.max_date,
        skip=skip,
        limit=search_params.per_page
    )
    total = await merchant_crud.count(db)

    return {
        "items": applications,
        "total": total,
        "page": search_params.page,
        "per_page": search_params.per_page,
        "total_pages": (total + search_params.per_page - 1) // search_params.per_page,
        "has_next": search_params.page * search_params.per_page < total,
        "has_prev": search_params.page > 1
    }


@router.get("/stats", response_model=MerchantApplicationStats)
async def _get_application_stats(
        db: AsyncSession = Depends(get_async_db),
        _: AdminUser = None
):
    """Get merchant application statistics (Admin only)."""
    return await merchant_crud.get_application_stats(db)


@router.patch("/{application_id}/status", response_model=MerchantApplicationResponse)
async def update_application_status(
        application_id: int,
        status_update: MerchantApplicationStatusUpdate,
        db: AsyncSession = Depends(get_async_db),
        admin_user: AdminUser = None
):
    """Update merchant application status (Admin only)."""

    if status_update.status == "approved":
        application = await merchant_crud.approve_application(
            db, application_id, admin_user.id, status_update.notes
        )
    elif status_update.status == "rejected":
        application = await merchant_crud.reject_application(
            db, application_id, admin_user.id, status_update.reason, status_update.notes
        )
    elif status_update.status == "suspended":
        application = await merchant_crud.suspend_application(
            db, application_id, admin_user.id, status_update.reason, status_update.notes
        )
    else:
        raise Exceptions.bad_request()

    if not application:
        raise Exceptions.not_found()

    return application


@router.get("/{application_id}", response_model=MerchantApplicationResponse)
async def get_application(
        application_id: int,
        db: AsyncSession = Depends(get_async_db),
        _: AdminUser = None
):
    """Get specific merchant application (Admin only)."""
    application = await merchant_crud.get(db, obj_id=application_id)
    if not application:
        raise Exceptions.not_found()
    return application