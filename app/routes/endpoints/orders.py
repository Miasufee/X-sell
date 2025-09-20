from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.order import OrderService
from app.schemas.order_schema import (
    CheckoutRequest, OrderResponse, OrderListResponse, 
    OrderStatusUpdate, OrderItemResponse
)
from app.schemas.product_schema import ProductListResponse
from app.api.dependencies import get_current_active_user, get_current_admin
from app.models.user import User
from app.models.order import OrderStatus

router = APIRouter()


@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    checkout_data: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Process checkout and create order"""
    service = OrderService(db)
    order = await service.checkout(current_user, checkout_data)
    
    # Convert to response format
    order_items = []
    for item in order.items:
        # Get product details if available
        product_response = None
        if item.product:
            primary_image = None
            if item.product.images:
                primary_img = next((img for img in item.product.images if img.is_primary), None)
                primary_image = primary_img.url if primary_img else item.product.images[0].url
            
            product_response = ProductListResponse(
                id=item.product.id,
                name=item.product.name,
                price=item.product.price,
                stock_quantity=item.product.stock_quantity,
                status=item.product.status,
                is_featured=item.product.is_featured,
                view_count=item.product.view_count,
                primary_image=primary_image,
                created_at=item.product.created_at
            )
        
        order_item = OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            product_sku=item.product_sku,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            product=product_response
        )
        order_items.append(order_item)
    
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        delivery_fee=order.delivery_fee,
        total_amount=order.total_amount,
        delivery_address=order.delivery_address,
        notes=order.notes,
        items=order_items,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.get("/", response_model=List[OrderListResponse])
async def get_user_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's order history"""
    service = OrderService(db)
    orders, total = await service.get_user_orders(current_user, skip, limit)
    
    # Convert to list response format
    order_list = []
    for order in orders:
        order_list.append(OrderListResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            total_amount=order.total_amount,
            items_count=len(order.items),
            created_at=order.created_at
        ))
    
    return order_list


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get order details"""
    service = OrderService(db)
    order = await service.get_order(order_id, current_user)
    
    # Convert to response format
    order_items = []
    for item in order.items:
        # Get product details if available
        product_response = None
        if item.product:
            primary_image = None
            if item.product.images:
                primary_img = next((img for img in item.product.images if img.is_primary), None)
                primary_image = primary_img.url if primary_img else item.product.images[0].url
            
            product_response = ProductListResponse(
                id=item.product.id,
                name=item.product.name,
                price=item.product.price,
                stock_quantity=item.product.stock_quantity,
                status=item.product.status,
                is_featured=item.product.is_featured,
                view_count=item.product.view_count,
                primary_image=primary_image,
                created_at=item.product.created_at
            )
        
        order_item = OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            product_sku=item.product_sku,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            product=product_response
        )
        order_items.append(order_item)
    
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        delivery_fee=order.delivery_fee,
        total_amount=order.total_amount,
        delivery_address=order.delivery_address,
        notes=order.notes,
        items=order_items,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update order status (admin/merchant only)"""
    service = OrderService(db)
    order = await service.update_order_status(
        order_id, status_update.status, current_user, status_update.notes
    )
    
    # Convert to response format (similar to get_order)
    order_items = []
    for item in order.items:
        order_item = OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            product_sku=item.product_sku,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price
        )
        order_items.append(order_item)
    
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        delivery_fee=order.delivery_fee,
        total_amount=order.total_amount,
        delivery_address=order.delivery_address,
        notes=order.notes,
        items=order_items,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.get("/status/{status}", response_model=List[OrderListResponse])
async def get_orders_by_status(
    status: OrderStatus,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get orders by status (admin only)"""
    service = OrderService(db)
    orders, total = await service.get_orders_by_status(status, skip, limit)
    
    # Convert to list response format
    order_list = []
    for order in orders:
        order_list.append(OrderListResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            total_amount=order.total_amount,
            items_count=len(order.items),
            created_at=order.created_at
        ))
    
    return order_list
