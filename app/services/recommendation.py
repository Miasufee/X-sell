from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text, or_
from sqlalchemy.orm import selectinload
import json
from app.models.product import Product, ProductStatus
from app.models.category import Category
from app.models.review import Review, Favorite
from app.models.order import Order, OrderItem
from app.models.user import User


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_content_based_recommendations(
        self, 
        product_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Get similar products based on category and tags"""
        # Get the reference product
        reference_product = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        reference_product = reference_product.scalar_one_or_none()
        
        if not reference_product:
            return []

        # Parse tags
        reference_tags = []
        if reference_product.tags:
            try:
                reference_tags = json.loads(reference_product.tags)
            except:
                reference_tags = []

        # Find similar products
        query = select(Product).options(
            selectinload(Product.images)
        ).where(
            and_(
                Product.id != product_id,
                Product.status == ProductStatus.ACTIVE,
                Product.stock_quantity > 0,
                or_(
                    Product.category_id == reference_product.category_id,
                    # Tag similarity would require more complex logic
                )
            )
        ).order_by(
            # Prioritize same category, then by popularity
            desc(Product.category_id == reference_product.category_id),
            desc(Product.view_count)
        ).limit(limit)

        result = await self.db.execute(query)
        similar_products = result.scalars().all()

        return [{'product': product, 'similarity_score': 0.8} for product in similar_products]

    async def get_collaborative_recommendations(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Get recommendations based on similar users' behavior (simplified)"""
        # Find products favorited by users who have similar favorites
        query = text("""
            SELECT DISTINCT p.*, 
                   COUNT(*) as common_favorites
            FROM products p
            JOIN favorites f1 ON p.id = f1.product_id
            JOIN favorites f2 ON f1.user_id = f2.user_id
            WHERE f2.user_id IN (
                SELECT DISTINCT f3.user_id 
                FROM favorites f3 
                WHERE f3.product_id IN (
                    SELECT product_id 
                    FROM favorites 
                    WHERE user_id = :user_id
                )
                AND f3.user_id != :user_id
            )
            AND p.id NOT IN (
                SELECT product_id 
                FROM favorites 
                WHERE user_id = :user_id
            )
            AND p.status = 'active'
            AND p.stock_quantity > 0
            GROUP BY p.id
            ORDER BY common_favorites DESC, p.view_count DESC
            LIMIT :limit
        """)

        result = await self.db.execute(query, {'user_id': user_id, 'limit': limit})
        products = result.fetchall()

        recommendations = []
        for row in products:
            product_id = row[0]  # Assuming id is first column
            product = await self.db.execute(
                select(Product).options(selectinload(Product.images))
                .where(Product.id == product_id)
            )
            product = product.scalar_one_or_none()
            if product:
                recommendations.append({
                    'product': product,
                    'confidence_score': min(1.0, row[-1] * 0.1)  # common_favorites
                })

        return recommendations

    async def get_trending_products(
        self, 
        period_days: int = 7, 
        limit: int = 20
    ) -> List[Dict]:
        """Get trending products based on recent views and orders"""
        # Calculate trending score based on recent activity
        query = text("""
            SELECT p.*, 
                   COALESCE(recent_views.view_increase, 0) as view_increase,
                   COALESCE(recent_orders.order_count, 0) as recent_orders,
                   (
                       COALESCE(recent_views.view_increase, 0) * 0.3 +
                       COALESCE(recent_orders.order_count, 0) * 0.7
                   ) as trending_score
            FROM products p
            LEFT JOIN (
                SELECT product_id, 
                       COUNT(*) as view_increase
                FROM (
                    SELECT id as product_id, view_count
                    FROM products 
                    WHERE updated_at >= NOW() - INTERVAL ':period_days days'
                ) recent_products
                GROUP BY product_id
            ) recent_views ON p.id = recent_views.product_id
            LEFT JOIN (
                SELECT oi.product_id,
                       COUNT(*) as order_count
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.created_at >= NOW() - INTERVAL ':period_days days'
                GROUP BY oi.product_id
            ) recent_orders ON p.id = recent_orders.product_id
            WHERE p.status = 'active' 
            AND p.stock_quantity > 0
            ORDER BY trending_score DESC, p.view_count DESC
            LIMIT :limit
        """)

        result = await self.db.execute(
            query, 
            {'period_days': period_days, 'limit': limit}
        )
        trending_data = result.fetchall()

        recommendations = []
        for row in trending_data:
            product_id = row[0]  # Assuming id is first column
            product = await self.db.execute(
                select(Product).options(selectinload(Product.images))
                .where(Product.id == product_id)
            )
            product = product.scalar_one_or_none()
            if product:
                recommendations.append({
                    'product': product,
                    'trending_score': float(row[-1]) if row[-1] else 0.0
                })

        return recommendations

    async def get_personalized_recommendations(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Get personalized recommendations combining multiple strategies"""
        recommendations = []
        
        # Get user's favorite categories
        favorite_categories = await self.db.execute(
            select(Product.category_id, func.count().label('count'))
            .join(Favorite, Product.id == Favorite.product_id)
            .where(Favorite.user_id == user_id)
            .group_by(Product.category_id)
            .order_by(desc('count'))
            .limit(3)
        )
        favorite_categories = favorite_categories.all()

        # Get recommendations from favorite categories
        if favorite_categories:
            category_ids = [cat[0] for cat in favorite_categories]
            category_products = await self.db.execute(
                select(Product).options(selectinload(Product.images))
                .where(
                    and_(
                        Product.category_id.in_(category_ids),
                        Product.status == ProductStatus.ACTIVE,
                        Product.stock_quantity > 0,
                        ~Product.id.in_(
                            select(Favorite.product_id).where(Favorite.user_id == user_id)
                        )
                    )
                )
                .order_by(desc(Product.view_count))
                .limit(limit // 2)
            )
            
            for product in category_products.scalars():
                recommendations.append({
                    'product': product,
                    'reason': 'Based on your favorite categories',
                    'confidence': 0.7
                })

        # Get collaborative filtering recommendations
        collab_recs = await self.get_collaborative_recommendations(user_id, limit // 2)
        for rec in collab_recs:
            rec['reason'] = 'Users with similar taste also liked'
            recommendations.append(rec)

        return recommendations[:limit]

    async def get_category_recommendations(
        self, 
        category_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Get popular products from a specific category"""
        query = select(Product).options(
            selectinload(Product.images)
        ).where(
            and_(
                Product.category_id == category_id,
                Product.status == ProductStatus.ACTIVE,
                Product.stock_quantity > 0
            )
        ).order_by(
            desc(Product.is_featured),
            desc(Product.view_count)
        ).limit(limit)

        result = await self.db.execute(query)
        products = result.scalars().all()

        return [{'product': product, 'popularity_score': product.view_count} for product in products]
