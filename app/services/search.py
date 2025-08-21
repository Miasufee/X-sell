from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text, desc
from sqlalchemy.orm import selectinload
import time
import json
from app.models.product import Product, ProductStatus
from app.models.category import Category
from app.models.shop import Shop
from app.models.review import Review
from app.schemas.search import SearchQuery, SearchResult
from app.utils.geolocation import get_bounding_box


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_products(
        self, 
        search_query: SearchQuery, 
        skip: int = 0, 
        limit: int = 20
    ) -> Tuple[List[Dict], int, int]:
        """Advanced product search with relevance scoring"""
        start_time = time.time()
        
        # Base query with joins
        query = select(
            Product,
            Shop,
            Category,
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('review_count')
        ).join(
            Shop, Product.shop_id == Shop.id
        ).join(
            Category, Product.category_id == Category.id
        ).outerjoin(
            Review, Product.id == Review.product_id
        ).options(
            selectinload(Product.images)
        ).where(
            and_(
                Product.status == ProductStatus.ACTIVE,
                Shop.is_active == True
            )
        ).group_by(Product.id, Shop.id, Category.id)

        count_query = select(func.count(Product.id)).join(
            Shop, Product.shop_id == Shop.id
        ).where(
            and_(
                Product.status == ProductStatus.ACTIVE,
                Shop.is_active == True
            )
        )

        conditions = []
        
        # Full-text search on name, description, and tags
        if search_query.q:
            search_term = f"%{search_query.q.lower()}%"
            search_conditions = or_(
                func.lower(Product.name).like(search_term),
                func.lower(Product.description).like(search_term),
                func.lower(Product.tags).like(search_term),
                func.lower(Category.name).like(search_term)
            )
            conditions.append(search_conditions)

        # Apply filters
        if search_query.category_id:
            conditions.append(Product.category_id == search_query.category_id)
        
        if search_query.min_price is not None:
            conditions.append(Product.price >= search_query.min_price)
        
        if search_query.max_price is not None:
            conditions.append(Product.price <= search_query.max_price)
        
        if search_query.in_stock:
            conditions.append(Product.stock_quantity > 0)
        
        if search_query.merchant_id:
            conditions.append(Product.merchant_id == search_query.merchant_id)
        
        if search_query.shop_id:
            conditions.append(Product.shop_id == search_query.shop_id)

        # Location-based filtering
        distance_expression = None
        if search_query.location_lat and search_query.location_lng:
            if search_query.radius_km:
                min_lat, max_lat, min_lon, max_lon = get_bounding_box(
                    search_query.location_lat, search_query.location_lng, search_query.radius_km
                )
                conditions.extend([
                    Shop.latitude.between(min_lat, max_lat),
                    Shop.longitude.between(min_lon, max_lon)
                ])
            
            # Calculate distance for sorting
            distance_expression = text("""
                (6371 * acos(
                    cos(radians(:lat)) * cos(radians(shops.latitude)) * 
                    cos(radians(shops.longitude) - radians(:lng)) + 
                    sin(radians(:lat)) * sin(radians(shops.latitude))
                ))
            """)

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Calculate relevance score
        relevance_score = self._build_relevance_score(search_query.q)
        query = query.add_columns(relevance_score.label('relevance_score'))
        
        if distance_expression:
            query = query.add_columns(distance_expression.label('distance_km'))

        # Apply sorting
        if search_query.sort_by == "relevance":
            query = query.order_by(desc(text('relevance_score')))
        elif search_query.sort_by == "price":
            if search_query.sort_order == "asc":
                query = query.order_by(Product.price.asc())
            else:
                query = query.order_by(Product.price.desc())
        elif search_query.sort_by == "distance" and distance_expression:
            query = query.order_by(text('distance_km'))
        elif search_query.sort_by == "popularity":
            query = query.order_by(desc(Product.view_count))
        elif search_query.sort_by == "newest":
            query = query.order_by(desc(Product.created_at))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute queries
        params = {}
        if search_query.location_lat and search_query.location_lng:
            params = {'lat': search_query.location_lat, 'lng': search_query.location_lng}

        result = await self.db.execute(query, params)
        search_results = result.all()

        count_result = await self.db.execute(count_query, params)
        total = count_result.scalar()

        # Process results
        processed_results = []
        for row in search_results:
            if distance_expression:
                product, shop, category, avg_rating, review_count, relevance_score, distance = row
                distance_km = round(distance, 2) if distance else None
            else:
                product, shop, category, avg_rating, review_count, relevance_score = row
                distance_km = None

            processed_results.append({
                'product': product,
                'shop': shop,
                'category': category,
                'avg_rating': float(avg_rating) if avg_rating else 0.0,
                'review_count': review_count or 0,
                'relevance_score': float(relevance_score),
                'distance_km': distance_km
            })

        search_time_ms = int((time.time() - start_time) * 1000)
        
        return processed_results, total, search_time_ms

    def _build_relevance_score(self, search_term: str):
        """Build relevance scoring expression"""
        if not search_term:
            return text("1.0")
        
        # Simple relevance scoring based on matches in different fields
        search_lower = search_term.lower()
        
        relevance_expression = text(f"""
            (
                CASE WHEN LOWER(products.name) LIKE '%{search_lower}%' THEN 10 ELSE 0 END +
                CASE WHEN LOWER(products.description) LIKE '%{search_lower}%' THEN 5 ELSE 0 END +
                CASE WHEN LOWER(products.tags) LIKE '%{search_lower}%' THEN 3 ELSE 0 END +
                CASE WHEN LOWER(categories.name) LIKE '%{search_lower}%' THEN 2 ELSE 0 END +
                CASE WHEN products.is_featured = true THEN 2 ELSE 0 END +
                (products.view_count * 0.01)
            )
        """)
        
        return relevance_expression

    async def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on product names and categories"""
        if len(query) < 2:
            return []
        
        search_term = f"%{query.lower()}%"
        
        # Get suggestions from product names
        product_suggestions = await self.db.execute(
            select(Product.name)
            .where(
                and_(
                    func.lower(Product.name).like(search_term),
                    Product.status == ProductStatus.ACTIVE
                )
            )
            .distinct()
            .limit(limit)
        )
        
        # Get suggestions from categories
        category_suggestions = await self.db.execute(
            select(Category.name)
            .where(
                and_(
                    func.lower(Category.name).like(search_term),
                    Category.is_active == True
                )
            )
            .distinct()
            .limit(limit)
        )
        
        suggestions = []
        suggestions.extend([row[0] for row in product_suggestions])
        suggestions.extend([row[0] for row in category_suggestions])
        
        return list(set(suggestions))[:limit]
