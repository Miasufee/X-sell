from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, merchants, products, shops, catalog, cart, orders, delivery, admin, reviews, categories

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(merchants.router, prefix="/merchants", tags=["merchants"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(shops.router, prefix="/shops", tags=["shops"])
api_router.include_router(catalog.router, prefix="/catalog", tags=["catalog"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(delivery.router, prefix="/delivery", tags=["delivery"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
