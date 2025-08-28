from app.models import (
    Product, ProductAttribute, ProductAttributeValue,
    ProductVariant, ProductVariantAttribute
)
from app.crud.base import CrudBase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional


class ProductCrud(CrudBase[Product]):
    def __init__(self):
        super().__init__(Product)


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
product_crud = ProductCrud()
attribute_crud = ProductAttributeCrud()
attribute_value_crud = ProductAttributeValueCrud()
variant_crud = ProductVariantCrud()
variant_attr_crud = ProductVariantAttributeCrud()
