from typing import List, Tuple
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid
import aiofiles
from app.repositories import ProductRepository, ProductImageRepository
from app.crud.category import CategoryRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductFilter
from app.models.product import Product, ProductImage
from app.models.user import User, UserRole
from app.core.config import settings


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.image_repo = ProductImageRepository(db)
        self.category_repo = CategoryRepository(db)

    async def create_product(self, product_data: ProductCreate, current_user: User) -> Product:
        """Create new product"""
        # Verify user is merchant or admin
        if current_user.role not in [UserRole.MERCHANT, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only merchants can create products"
            )
        
        # Verify category exists
        category = await self.category_repo.get_by_id(product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if SKU already exists
        if product_data.sku:
            existing_product = await self.product_repo.get_by_sku(product_data.sku)
            if existing_product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU already exists"
                )
        
        return await self.product_repo.create(product_data, current_user.id)

    async def get_product(self, product_id: int, increment_views: bool = False) -> Product:
        """Get product by ID"""
        product = await self.product_repo.get_by_id(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if increment_views:
            await self.product_repo.increment_view_count(product)
        
        return product

    async def update_product(self, product_id: int, product_data: ProductUpdate, current_user: User) -> Product:
        """Update product"""
        product = await self.get_product(product_id)
        
        # Check permissions
        if current_user.role != UserRole.ADMIN and product.merchant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this product"
            )
        
        # Verify category if being updated
        if product_data.category_id:
            category = await self.category_repo.get_by_id(product_data.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
        
        # Check SKU uniqueness if being updated
        if product_data.sku and product_data.sku != product.sku:
            existing_product = await self.product_repo.get_by_sku(product_data.sku)
            if existing_product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU already exists"
                )
        
        return await self.product_repo.update(product, product_data)

    async def delete_product(self, product_id: int, current_user: User) -> None:
        """Delete product"""
        product = await self.get_product(product_id)
        
        # Check permissions
        if current_user.role != UserRole.ADMIN and product.merchant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this product"
            )
        
        await self.product_repo.delete(product)

    async def get_products(
        self, 
        filters: ProductFilter, 
        skip: int = 0, 
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Product], int]:
        """Get filtered list of products"""
        return await self.product_repo.get_list(filters, skip, limit, sort_by, sort_order)

    async def get_merchant_products(self, merchant_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[Product], int]:
        """Get products by merchant"""
        return await self.product_repo.get_by_merchant(merchant_id, skip, limit)

    async def upload_product_image(self, product_id: int, file: UploadFile, current_user: User) -> ProductImage:
        """Upload product image"""
        product = await self.get_product(product_id)
        
        # Check permissions
        if current_user.role != UserRole.ADMIN and product.merchant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload images for this product"
            )
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size must be less than {settings.MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, "products", filename)
        
        # Ensure upload directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create image record
        image_data = {
            'url': f"/uploads/products/{filename}",
            'alt_text': f"{product.name} image",
            'is_primary': False,
            'sort_order': 0
        }
        
        return await self.image_repo.create(product_id, image_data)

    async def delete_product_image(self, product_id: int, image_id: int, current_user: User) -> None:
        """Delete product image"""
        product = await self.get_product(product_id)
        
        # Check permissions
        if current_user.role != UserRole.ADMIN and product.merchant_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete images for this product"
            )
        
        image = await self.image_repo.get_by_id(image_id)
        if not image or image.product_id != product_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        # Delete file from filesystem
        if image.url.startswith('/uploads/'):
            file_path = image.url[1:]  # Remove leading slash
            if os.path.exists(file_path):
                os.remove(file_path)
        
        await self.image_repo.delete(image)

    async def get_product_images(self, product_id: int) -> List[ProductImage]:
        """Get all images for a product"""
        product = await self.get_product(product_id)
        return await self.image_repo.get_by_product(product_id)
