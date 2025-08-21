from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.shop import ShopService
from app.schemas.shop import ShopCreate, ShopUpdate, ShopResponse, ShopWithDistance, NearbyShopsResponse
from app.api.dependencies import get_current_user, get_current_merchant
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
async def create_shop(
    shop_data: ShopCreate,
    current_user: User = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db)
):
    """Create a new shop"""
    service = ShopService(db)
    shop = await service.create_shop(shop_data, current_user)
    return ShopResponse.model_validate(shop)


@router.get("/", response_model=List[ShopResponse])
async def list_shops(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Get list of shops"""
    service = ShopService(db)
    shops, total = await service.get_shops(skip, limit, active_only)
    return [ShopResponse.model_validate(shop) for shop in shops]


@router.get("/nearby", response_model=NearbyShopsResponse)
async def find_nearby_shops(
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lng: float = Query(..., description="Longitude", ge=-180, le=180),
    radius_km: int = Query(10, description="Search radius in kilometers", ge=1, le=50),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Find shops near a location"""
    service = ShopService(db)
    shops_with_distance, total = await service.find_nearby_shops(lat, lng, radius_km, skip, limit)
    
    # Convert to response format
    shops_response = []
    for item in shops_with_distance:
        shop = item['shop']
        distance = item['distance_km']
        
        shop_with_distance = ShopWithDistance(
            id=shop.id,
            name=shop.name,
            description=shop.description,
            address=shop.address,
            latitude=shop.latitude,
            longitude=shop.longitude,
            phone=shop.phone,
            email=shop.email,
            merchant_id=shop.merchant_id,
            is_active=shop.is_active,
            created_at=shop.created_at,
            updated_at=shop.updated_at,
            distance_km=distance
        )
        shops_response.append(shop_with_distance)
    
    return NearbyShopsResponse(
        shops=shops_response,
        total=total,
        search_location={"latitude": lat, "longitude": lng},
        radius_km=radius_km
    )


@router.get("/{shop_id}", response_model=ShopResponse)
async def get_shop(
    shop_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get shop by ID"""
    service = ShopService(db)
    shop = await service.get_shop(shop_id)
    return ShopResponse.model_validate(shop)


@router.put("/{shop_id}", response_model=ShopResponse)
async def update_shop(
    shop_id: int,
    shop_data: ShopUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update shop"""
    service = ShopService(db)
    shop = await service.update_shop(shop_id, shop_data, current_user)
    return ShopResponse.model_validate(shop)


@router.delete("/{shop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shop(
    shop_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete shop"""
    service = ShopService(db)
    await service.delete_shop(shop_id, current_user)


@router.get("/merchant/{merchant_id}", response_model=List[ShopResponse])
async def get_merchant_shops(
    merchant_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get shops by merchant"""
    service = ShopService(db)
    shops, total = await service.get_merchant_shops(merchant_id, skip, limit)
    return [ShopResponse.model_validate(shop) for shop in shops]
