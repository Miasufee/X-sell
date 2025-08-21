from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import CartRepository
from app.repositories import ProductRepository
from app.models.cart import Cart, CartItem
from app.models.user import User


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)

    async def get_cart(self, user: User) -> Cart:
        """Get user's cart"""
        return await self.cart_repo.get_or_create_cart(user.id)

    async def add_to_cart(self, user: User, product_id: int, quantity: int) -> CartItem:
        """Add product to cart"""
        # Get product
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check if product is active and in stock
        if product.status != 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is not available"
            )
        
        if product.stock_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock_quantity} items available in stock"
            )
        
        # Get or create cart
        cart = await self.cart_repo.get_or_create_cart(user.id)
        
        # Add item to cart
        return await self.cart_repo.add_item(cart, product, quantity)

    async def update_cart_item(self, user: User, item_id: int, quantity: int) -> CartItem:
        """Update cart item quantity"""
        cart = await self.cart_repo.get_or_create_cart(user.id)
        
        # Get cart item
        cart_item = await self.cart_repo.get_cart_item(cart.id, item_id)
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        
        # Check stock availability
        product = await self.product_repo.get_by_id(cart_item.product_id)
        if product and product.stock_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock_quantity} items available in stock"
            )
        
        return await self.cart_repo.update_item_quantity(cart_item, quantity)

    async def remove_from_cart(self, user: User, item_id: int) -> None:
        """Remove item from cart"""
        cart = await self.cart_repo.get_or_create_cart(user.id)
        
        # Get cart item
        cart_item = await self.cart_repo.get_cart_item(cart.id, item_id)
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        
        await self.cart_repo.remove_item(cart_item)

    async def clear_cart(self, user: User) -> None:
        """Clear all items from cart"""
        cart = await self.cart_repo.get_or_create_cart(user.id)
        await self.cart_repo.clear_cart(cart)
