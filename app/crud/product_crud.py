import json

from app.models import (
    Product, ProductAttribute, ProductAttributeValue,
    ProductVariant, ProductVariantAttribute, ProductStatus, ProductImage
)
from app.crud.crud_base import CrudBase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update, or_
from typing import List, Optional, Any, Coroutine, Sequence, Dict


class ProductService(CrudBase[Product]):
    """Service for handling product operations."""

    def __init__(self):
        super().__init__(Product)

    async def create_product(
            self,
            db: AsyncSession,
            merchant_id: int,
            shop_id: int,
            category_id: int,
            name: str,
            description: str,
            tags: Optional[List[str]] = None,
            status: ProductStatus = ProductStatus.DRAFT,
            is_featured: bool = False
    ) -> Product:
        """Create a new product."""
        product_data = {
            "merchant_id": merchant_id,
            "shop_id": shop_id,
            "category_id": category_id,
            "name": name,
            "description": description,
            "tags": json.dumps(tags) if tags else None,
            "status": status,
            "is_featured": is_featured
        }

        return await self.create(db, **product_data)

    async def get_shop_products(
            self,
            db: AsyncSession,
            shop_id: int,
            status: Optional[ProductStatus] = None,
            active_only: bool = True,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[Product]:
        """Get products for a specific shop."""
        filters = {"shop_id": shop_id}
        if status:
            filters["status"] = status
        elif active_only:
            filters["status"] = ProductStatus.ACTIVE

        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters=filters,
            order_by=["-is_featured", "name"]
        )

    async def get_merchant_products(
            self,
            db: AsyncSession,
            merchant_id: int,
            status: Optional[ProductStatus] = None,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[Product]:
        """Get all products for a merchant across all shops."""
        filters = {"merchant_id": merchant_id}
        if status:
            filters["status"] = status

        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters=filters,
            order_by=["shop_id", "name"]
        )

    async def get_product_with_details(
            self,
            db: AsyncSession,
            product_id: int
    ) -> Optional[Product]:
        """Get product with all related details."""
        from sqlalchemy.orm import joinedload, selectinload

        stmt = select(Product).options(
            joinedload(Product.shop),
            joinedload(Product.category),
            joinedload(Product.merchant),
            selectinload(Product.images),
            selectinload(Product.variants).selectinload(ProductVariant.attributes),
            selectinload(Product.attributes).selectinload(ProductAttribute.values)
        ).where(Product.id == product_id)

        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def update_product_status(
            self,
            db: AsyncSession,
            product_id: int,
            merchant_id: int,
            new_status: ProductStatus
    ) -> Optional[Product]:
        """Update product status with merchant validation."""
        product = await self.get(db, obj_id=product_id)
        if not product or product.merchant_id != merchant_id:
            return None

        return await self.update(db, obj_id=product_id, status=new_status)

    async def toggle_featured_status(
            self,
            db: AsyncSession,
            product_id: int,
            merchant_id: int
    ) -> Optional[Product]:
        """Toggle product featured status."""
        product = await self.get(db, obj_id=product_id)
        if not product or product.merchant_id != merchant_id:
            return None

        new_featured = not product.is_featured
        return await self.update(db, obj_id=product_id, is_featured=new_featured)

    async def increment_view_count(
            self,
            db: AsyncSession,
            product_id: int
    ) -> None:
        """Increment product view count."""
        await self.bulk_update(
            db,
            filters={"id": product_id},
            update_values={"view_count": Product.view_count + 1}
        )

    async def search_products(
            self,
            db: AsyncSession,
            search_term: Optional[str] = None,
            category_id: Optional[int] = None,
            shop_id: Optional[int] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            status: ProductStatus = ProductStatus.ACTIVE,
            featured_only: bool = False,
            skip: int = 0,
            limit: int = 100
    ) -> Sequence[Product]:
        """Search products with various filters."""
        conditions = [Product.status == status]

        if category_id:
            conditions.append(Product.category_id == category_id)
        if shop_id:
            conditions.append(Product.shop_id == shop_id)
        if featured_only:
            conditions.append(Product.is_featured == True)

        # Text search
        if search_term:
            search_condition = or_(
                Product.name.ilike(f"%{search_term}%"),
                Product.description.ilike(f"%{search_term}%"),
                Product.tags.ilike(f"%{search_term}%")
            )
            conditions.append(search_condition)

        # Price filtering (through variants)
        if min_price is not None or max_price is not None:
            from app.models import ProductVariant
            price_subquery = select(ProductVariant.product_id).where(
                and_(
                    ProductVariant.product_id == Product.id,
                    *(min_price is not None and [ProductVariant.price >= min_price] or []),
                    *(max_price is not None and [ProductVariant.price <= max_price] or [])
                )
            ).exists()
            conditions.append(price_subquery)

        where_clause = and_(*conditions)

        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            where_clause=where_clause,
            order_by=["-is_featured", "-view_count", "name"]
        )

    async def get_featured_products(
            self,
            db: AsyncSession,
            limit: int = 20
    ) -> Sequence[Product]:
        """Get featured active products."""
        return await self.get_multi(
            db,
            filters={
                "is_featured": True,
                "status": ProductStatus.ACTIVE
            },
            limit=limit,
            order_by="-view_count"
        )

    async def get_popular_products(
            self,
            db: AsyncSession,
            limit: int = 20
    ) -> Sequence[Product]:
        """Get popular active products."""
        return await self.get_multi(
            db,
            filters={"status": ProductStatus.ACTIVE},
            limit=limit,
            order_by="-view_count"
        )

    async def get_product_stats(
            self,
            db: AsyncSession,
            merchant_id: Optional[int] = None,
            shop_id: Optional[int] = None
    ) -> Dict[str, int]:
        """Get product statistics."""
        stats = {}
        filters = {}

        if merchant_id:
            filters["merchant_id"] = merchant_id
        if shop_id:
            filters["shop_id"] = shop_id

        # Count by status
        for status in ProductStatus:
            count = await self.count(db, filters={**filters, "status": status})
            stats[f"{status.value}_count"] = count

        # Total count
        stats["total_count"] = await self.count(db, filters=filters)

        # Featured count
        stats["featured_count"] = await self.count(
            db,
            filters={**filters, "is_featured": True, "status": ProductStatus.ACTIVE}
        )

        return stats

    async def add_product_image(
            self,
            db: AsyncSession,
            product_id: int,
            merchant_id: int,
            url: str,
            alt_text: Optional[str] = None,
            is_primary: bool = False
    ) -> Optional[ProductImage]:
        """Add image to product with merchant validation."""
        product = await self.get(db, obj_id=product_id)
        if not product or product.merchant_id != merchant_id:
            return None

        # If setting as primary, remove primary status from other images
        if is_primary:
            await db.execute(
                update(ProductImage)
                .where(ProductImage.product_id == product_id)
                .values(is_primary=False)
            )

        image_data = {
            "product_id": product_id,
            "url": url,
            "alt_text": alt_text,
            "is_primary": is_primary
        }

        image_service = CrudBase(ProductImage)
        return await image_service.create(db, **image_data)

    async def create_product_variant(
            self,
            db: AsyncSession,
            product_id: int,
            merchant_id: int,
            sku: str,
            price: float,
            stock_quantity: int = 0,
            weight: Optional[float] = None
    ) -> Optional[ProductVariant]:
        """Create variant for product with merchant validation."""
        product = await self.get(db, obj_id=product_id)
        if not product or product.merchant_id != merchant_id:
            return None

        variant_data = {
            "product_id": product_id,
            "sku": sku,
            "price": price,
            "stock_quantity": stock_quantity,
            "weight": weight
        }

        variant_service = CrudBase(ProductVariant)
        return await variant_service.create(db, **variant_data)

    async def bulk_update_products(
            self,
            db: AsyncSession,
            merchant_id: int,
            product_ids: List[int],
            **update_data
    ) -> int:
        """Bulk update products for a merchant."""
        return await self.bulk_update(
            db,
            filters={"id": product_ids, "merchant_id": merchant_id},
            update_values=update_data
        )


class ProductAttributeCrud(CrudBase[ProductAttribute]):
    def __init__(self):
        super().__init__(ProductAttribute)


class ProductAttributeValueCrud(CrudBase[ProductAttributeValue]):
    def __init__(self):
        super().__init__(ProductAttributeValue)


class ProductVariantCrud(CrudBase[ProductVariant]):
    def __init__(self):
        super().__init__(ProductVariant)


    async def get_variant_by_attributes(
        self, db: AsyncSession, product_id: int, attribute_value_ids: List[int]
    ) -> Optional[ProductVariant]:
        """
        Get a variant by its attribute combination.
        Prevents duplicate variants like (Red + Small).
        """
        stmt = (
            select(self.model)
            .join(self.model.attributes)
            .where(self.model.product_id.is_(product_id))
            .group_by(self.model.id)
            .having(
                func.array_agg(ProductVariantAttribute.attribute_value_id).op("@>")(attribute_value_ids)
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()


class ProductVariantAttributeCrud(CrudBase[ProductVariantAttribute]):
    def __init__(self):
        super().__init__(ProductVariantAttribute)


# Instantiate crud objects

attribute_crud = ProductAttributeCrud()
attribute_value_crud = ProductAttributeValueCrud()
variant_crud = ProductVariantCrud()
variant_attr_crud = ProductVariantAttributeCrud()
