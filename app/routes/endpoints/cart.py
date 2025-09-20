from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.crud.cart_crud import cart_crud, cart_item_crud

from app.core.dependencies import RegularUser
from app.schemas import ProductListResponse
from app.schemas.cart_schema import (
    CartResponse, CartItemResponse, AddToCartRequest, 
    UpdateCartItemRequest
)


router = APIRouter()


@router.get("/", response_model=CartResponse)
async def get_cart(
    current_user: RegularUser = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get user's shopping cart"""
    cart = await cart_crud.get(db, user_id=current_user)
    
    # Convert cart items to response format
    cart_items = []
    for item in cart.items:
        # Get primary image
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
        
        cart_item = CartItemResponse(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            product=product_response,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        cart_items.append(cart_item)
    
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        total_amount=cart.total_amount,
        items=cart_items,
        items_count=len(cart_items),
        created_at=cart.created_at,
        updated_at=cart.updated_at
    )


@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    request: AddToCartRequest,
    current_user: RegularUser = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Add item to cart"""
    cart_item = await cart_crud.add_to_cart(current_user, request.product_id, request.quantity)
    
    # Get primary image
    primary_image = None
    if cart_item.product.images:
        primary_img = next((img for img in cart_item.product.images if img.is_primary), None)
        primary_image = primary_img.url if primary_img else cart_item.product.images[0].url
    
    product_response = ProductListResponse(
        id=cart_item.product.id,
        name=cart_item.product.name,
        price=cart_item.product.price,
        stock_quantity=cart_item.product.stock_quantity,
        status=cart_item.product.status,
        is_featured=cart_item.product.is_featured,
        view_count=cart_item.product.view_count,
        primary_image=primary_image,
        created_at=cart_item.product.created_at
    )
    
    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        unit_price=cart_item.unit_price,
        total_price=cart_item.total_price,
        product=product_response,
        created_at=cart_item.created_at,
        updated_at=cart_item.updated_at
    )


@router.put("/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: int,
    request: UpdateCartItemRequest,
    current_user: RegularUser = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Update cart item quantity"""
    cart_item = await cart_item_crud.update_cart_item(current_user, item_id, request.quantity)
    
    # Get primary image
    primary_image = None
    if cart_item.product.images:
        primary_img = next((img for img in cart_item.product.images if img.is_primary), None)
        primary_image = primary_img.url if primary_img else cart_item.product.images[0].url
    
    product_response = ProductListResponse(
        id=cart_item.product.id,
        name=cart_item.product.name,
        price=cart_item.product.price,
        stock_quantity=cart_item.product.stock_quantity,
        status=cart_item.product.status,
        is_featured=cart_item.product.is_featured,
        view_count=cart_item.product.view_count,
        primary_image=primary_image,
        created_at=cart_item.product.created_at
    )
    
    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        unit_price=cart_item.unit_price,
        total_price=cart_item.total_price,
        product=product_response,
        created_at=cart_item.created_at,
        updated_at=cart_item.updated_at
    )


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    item_id: int,
    current_user: RegularUser = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Remove item from cart"""

    await cart_crud.remove_from_cart(current_user, item_id)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: RegularUser = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Clear all items from cart"""
    await cart_crud.clear_cart(current_user)
