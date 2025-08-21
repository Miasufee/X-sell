
from .base import CrudBase
from app.models.product import Product, ProductImage, ProductStatus


class ProductCrud(CrudBase[Product]):
    def __init__(self):
        super().__init__(Product)


class ProductImageCrud(CrudBase[ProductImage]):
    def __init__(self):
        super().__init__(ProductImage)



# Create instances for easy import
product_crud = ProductCrud()
product_image_crud = ProductImageCrud()
