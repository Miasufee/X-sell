from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas import (
    ShopCreate,
    ShopResponse,
    ShopUpdate,
    ShopSearch,
    ShopStats,
    PaginatedResponse
)
from app.crud.shop_crud import ShopService
from app.core.dependencies import CurrentUser
from app.crud.merchant_crud import MerchantService

router = APIRouter(prefix="/shops", tags=["shops"])


@router.post("/", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
async def create_shop(
        shop_data: ShopCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Create a new shop (Merchant only)."""
    # Check if user is approved merchant
    merchant_service = MerchantService()
    application = await merchant_service.get_user_application(db, current_user.id)
    if not application or application.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need to be an approved merchant to create a shop"
        )

    service = ShopService()
    return await service.create_shop(db, current_user.id, **shop_data.model_dump())


@router.get("/my-shops", response_model=List[ShopResponse])
async def get_my_shops(
        active_only: bool = True,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Get current user's shops."""
    service = ShopService()
    return await service.get_merchant_shops(db, current_user.id, active_only)


@router.get("/", response_model=PaginatedResponse[ShopResponse])
async def search_shops(
        search_params: ShopSearch = Depends(),
        db: AsyncSession = Depends(get_async_db)
):
    """Search shops with various filters."""
    service = ShopService()
    skip = (search_params.page - 1) * search_params.per_page

    shops = await service.search_shops(
        db,
        search_term=search_params.search_term,
        latitude=search_params.latitude,
        longitude=search_params.longitude,
        radius_km=search_params.radius_km,
        active_only=search_params.active_only,
        skip=skip,
        limit=search_params.per_page
    )

    total = await service.count(db, filters={"is_active": True} if search_params.active_only else {})

    return {
        "items": shops,
        "total": total,
        "page": search_params.page,
        "per_page": search_params.per_page,
        "total_pages": (total + search_params.per_page - 1) // search_params.per_page,
        "has_next": search_params.page * search_params.per_page < total,
        "has_prev": search_params.page > 1
    }


@router.get("/nearby", response_model=List[ShopResponse])
async def get_nearby_shops(
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        limit: int = 50,
        db: AsyncSession = Depends(get_async_db)
):
    """Get shops near a specific location."""
    service = ShopService()
    return await service.get_nearby_shops(db, latitude, longitude, radius_km, limit)


@router.get("/{shop_id}", response_model=ShopResponse)
async def get_shop(
        shop_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """Get specific shop details."""
    service = ShopService()
    shop = await service.get(db, obj_id=shop_id)
    if not shop or not shop.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found"
        )
    return shop


@router.put("/{shop_id}", response_model=ShopResponse)
async def update_shop(
        shop_id: int,
        shop_data: ShopUpdate,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Update shop details (Shop owner only)."""
    service = ShopService()
    shop = await service.update_shop(db, shop_id, current_user.id, **shop_data.model_dump(exclude_unset=True))
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found or access denied"
        )
    return shop


@router.patch("/{shop_id}/toggle-status", response_model=ShopResponse)
async def toggle_shop_status(
        shop_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Toggle shop active status (Shop owner only)."""
    service = ShopService()
    shop = await service.toggle_shop_status(db, shop_id, current_user.id)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found or access denied"
        )
    return shop


@router.get("/stats/my-shops", response_model=ShopStats)
async def get_my_shop_stats(
        db: AsyncSession = Depends(get_async_db),
        current_user: CurrentUser = Depends()
):
    """Get current user's shop statistics."""
    service = ShopService()
    return await service.get_shop_stats(db, current_user.id)