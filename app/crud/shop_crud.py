from math import cos

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func
from typing import Optional, List, Dict, Any, Coroutine, Sequence
from .crud_base import CrudBase
from app.models import Shop, User
from app.core.dependencies import CurrentUser, AdminUser


class ShopService(CrudBase[Shop]):
    """Service for handling shop operations."""

    def __init__(self):
        super().__init__(Shop)

    async def create_shop(
            self,
            db: AsyncSession,
            merchant_id: int,
            name: str,
            address: str,
            latitude: float,
            longitude: float,
            description: Optional[str] = None,
            phone: Optional[str] = None,
            email: Optional[str] = None
    ) -> Shop:
        """Create a new shop for a merchant."""
        shop_data = {
            "merchant_id": merchant_id,
            "name": name,
            "description": description,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
            "phone": phone,
            "email": email,
            "is_active": True
        }

        return await self.create(db, **shop_data)

    async def get_merchant_shops(
            self,
            db: AsyncSession,
            merchant_id: int,
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[Shop]:
        """Get all shops for a specific merchant."""
        filters = {"merchant_id": merchant_id}
        if active_only:
            filters["is_active"] = True

        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="name"
        )

    async def get_shop_with_merchant(
            self,
            db: AsyncSession,
            shop_id: int
    ) -> Optional[Shop]:
        """Get shop with merchant information."""
        from sqlalchemy.orm import joinedload

        stmt = select(Shop).options(
            joinedload(Shop.merchant)
        ).where(Shop.id == shop_id)

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_shop(
            self,
            db: AsyncSession,
            shop_id: int,
            merchant_id: int,
            **update_data
    ) -> Optional[Shop]:
        """Update shop with merchant validation."""
        shop = await self.get(db, obj_id=shop_id)
        if not shop or shop.merchant_id != merchant_id:
            return None

        return await self.update(db, obj_id=shop_id, **update_data)

    async def toggle_shop_status(
            self,
            db: AsyncSession,
            shop_id: int,
            merchant_id: int
    ) -> Optional[Shop]:
        """Toggle shop active status."""
        shop = await self.get(db, obj_id=shop_id)
        if not shop or shop.merchant_id != merchant_id:
            return None

        new_status = not shop.is_active
        return await self.update(db, obj_id=shop_id, is_active=new_status)

    async def search_shops(
            self,
            db: AsyncSession,
            search_term: Optional[str] = None,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
            radius_km: float = 10.0,
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[Shop]:
        """Search shops with location-based filtering."""
        conditions = []

        if active_only:
            conditions.append(Shop.is_active == True)

        # Text search
        if search_term:
            search_condition = or_(
                Shop.name.ilike(f"%{search_term}%"),
                Shop.description.ilike(f"%{search_term}%"),
                Shop.address.ilike(f"%{search_term}%")
            )
            conditions.append(search_condition)

        # Location-based search (approximate)
        if latitude and longitude:
            # Simple bounding box for demonstration
            # In production, use PostGIS or similar for accurate distance calculations
            lat_range = 0.009 * radius_km  # ~1km per 0.009 degrees
            lng_range = 0.009 * radius_km / abs(cos(latitude * 0.0174533))

            conditions.extend([
                Shop.latitude.between(latitude - lat_range, latitude + lat_range),
                Shop.longitude.between(longitude - lng_range, longitude + lng_range)
            ])

        where_clause = and_(*conditions) if conditions else None

        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            where_clause=where_clause,
            order_by="name"
        )

    async def get_nearby_shops(
            self,
            db: AsyncSession,
            latitude: float,
            longitude: float,
            radius_km: float = 10.0,
            limit: int = 50
    ) -> Sequence[Shop]:
        """Get shops near a specific location."""
        # Simple bounding box approach
        lat_range = 0.009 * radius_km
        lng_range = 0.009 * radius_km / abs(cos(latitude * 0.0174533))

        where_clause = and_(
            Shop.is_active == True,
            Shop.latitude.between(latitude - lat_range, latitude + lat_range),
            Shop.longitude.between(longitude - lng_range, longitude + lng_range)
        )

        return await self.get_multi(
            db,
            where_clause=where_clause,
            limit=limit,
            order_by="name"
        )

    async def get_shop_stats(
            self,
            db: AsyncSession,
            merchant_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get shop statistics."""
        stats = {}

        # Total shops
        if merchant_id:
            stats["total_shops"] = await self.count(db, filters={"merchant_id": merchant_id})
            stats["active_shops"] = await self.count(
                db,
                filters={"merchant_id": merchant_id, "is_active": True}
            )
        else:
            stats["total_shops"] = await self.count(db)
            stats["active_shops"] = await self.count(db, filters={"is_active": True})

        return stats

    async def bulk_update_shops(
            self,
            db: AsyncSession,
            merchant_id: int,
            shop_ids: List[int],
            **update_data
    ) -> int:
        """Bulk update shops for a merchant."""
        return await self.bulk_update(
            db,
            filters={"id": shop_ids, "merchant_id": merchant_id},
            update_values=update_data
        )