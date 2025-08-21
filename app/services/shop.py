from typing import List, Tuple, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import ShopRepository
from app.schemas.shop import ShopCreate, ShopUpdate
from app.models.shop import Shop
from app.models.user import User, UserRole


class ShopService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.shop_repo = ShopRepository(db)

    async def create_shop(self, shop_data: ShopCreate, current_user: User) -> Shop:
        """Create new shop"""
        # Verify user is merchant or admin
        if current_user.role not in [UserRole.MERCHANT, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only merchants can create shops"
            )
        
        return await self.shop_repo.create(shop_data, current_user.id)

    async def get_shop(self, shop_id: int) -> Shop:
        """Get shop by ID"""
        shop = await self.shop_repo.get_by_id(shop_id)
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )
        
        return shop

    async def update_shop(self, shop_id: int, shop_data: ShopUpdate, current_user: User) -> Shop:
        """Update shop"""
        shop = await self.get_shop(shop_id)
        
        # Check permissions
        if current_user.role != UserRole.ADMIN and shop.merchant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this shop"
            )
        
        return await self.shop_repo.update(shop, shop_data)

    async def delete_shop(self, shop_id: int, current_user: User) -> None:
        """Delete shop"""
        shop = await self.get_shop(shop_id)
        
        # Check permissions
        if current_user.role != UserRole.ADMIN and shop.merchant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this shop"
            )
        
        await self.shop_repo.delete(shop)

    async def get_shops(self, skip: int = 0, limit: int = 20, active_only: bool = True) -> Tuple[List[Shop], int]:
        """Get list of shops"""
        return await self.shop_repo.get_list(skip, limit, active_only)

    async def get_merchant_shops(self, merchant_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[Shop], int]:
        """Get shops by merchant"""
        return await self.shop_repo.get_by_merchant(merchant_id, skip, limit)

    async def find_nearby_shops(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[dict], int]:
        """Find shops within radius"""
        return await self.shop_repo.find_nearby_shops(latitude, longitude, radius_km, skip, limit)

    async def find_nearby_products(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None
    ) -> Tuple[List[dict], int]:
        """Find products from nearby shops"""
        return await self.shop_repo.find_nearby_products(
            latitude, longitude, radius_km, skip, limit, category_id
        )
