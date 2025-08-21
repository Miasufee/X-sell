from typing import List, Tuple, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import OrderRepository
from app.repositories import CartRepository
from app.services.delivery import DeliveryService
from app.schemas.order import CheckoutRequest
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.delivery_service = DeliveryService()

    async def checkout(self, user: User, checkout_data: CheckoutRequest) -> Order:
        """Process checkout and create order"""
        # Get user's cart
        cart = await self.cart_repo.get_or_create_cart(user.id)
        
        if not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Validate stock availability for all items
        for item in cart.items:
            if item.product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {item.product.name}"
                )
        
        # Calculate delivery fee if location provided
        delivery_fee = 0.0
        if checkout_data.delivery_lat and checkout_data.delivery_lng:
            # For simplicity, use first shop's location for delivery calculation
            # In a real system, you'd handle multiple shops differently
            first_shop = cart.items[0].product.shop
            delivery_estimate = self.delivery_service.estimate_delivery_cost_and_distance(
                first_shop.latitude, first_shop.longitude,
                checkout_data.delivery_lat, checkout_data.delivery_lng
            )
            delivery_fee = delivery_estimate['total_cost']
        
        # Calculate tax (simple 8% tax rate)
        tax_amount = cart.total_amount * 0.08
        
        # Create order
        order = await self.order_repo.create_order_from_cart(
            cart=cart,
            delivery_address=checkout_data.delivery_address,
            delivery_fee=delivery_fee,
            tax_amount=tax_amount,
            notes=checkout_data.notes
        )
        
        # Reduce product stock
        await self.order_repo.reduce_product_stock(order)
        
        # Clear cart
        await self.cart_repo.clear_cart(cart)
        
        return order

    async def get_order(self, order_id: int, user: User) -> Order:
        """Get order by ID"""
        order = await self.order_repo.get_by_id(order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check permissions
        if user.role != UserRole.ADMIN and order.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this order"
            )
        
        return order

    async def get_user_orders(
        self, 
        user: User, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Order], int]:
        """Get user's order history"""
        return await self.order_repo.get_user_orders(user.id, skip, limit)

    async def update_order_status(
        self, 
        order_id: int, 
        status: OrderStatus, 
        user: User,
        notes: Optional[str] = None
    ) -> Order:
        """Update order status (admin/merchant only)"""
        order = await self.order_repo.get_by_id(order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Check permissions
        if user.role not in [UserRole.ADMIN, UserRole.MERCHANT]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update order status"
            )
        
        # Merchants can only update orders for their products
        if user.role == UserRole.MERCHANT:
            merchant_product_ids = [item.product_id for item in order.items 
                                 if item.product.merchant_id == user.id]
            if not merchant_product_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this order"
                )
        
        return await self.order_repo.update_status(order, status, notes)

    async def get_orders_by_status(
        self, 
        status: OrderStatus, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Order], int]:
        """Get orders by status (admin only)"""
        return await self.order_repo.get_orders_by_status(status, skip, limit)
