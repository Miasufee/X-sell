from typing import Dict
from app.utils.geolocation import calculate_delivery_distance, estimate_delivery_cost
from app.core.config import settings


class DeliveryService:
    def __init__(self):
        pass

    def estimate_delivery_cost_and_distance(
        self,
        pickup_lat: float,
        pickup_lon: float,
        delivery_lat: float,
        delivery_lon: float,
        weight_kg: float = None
    ) -> Dict:
        """
        Estimate delivery cost and calculate distance
        """
        # Calculate distance
        distance_km = calculate_delivery_distance(pickup_lat, pickup_lon, delivery_lat, delivery_lon)
        
        # Calculate cost
        base_cost = estimate_delivery_cost(
            distance_km, 
            settings.DELIVERY_BASE_FEE, 
            settings.DELIVERY_RATE_PER_KM
        )
        
        # Add weight-based fee if applicable
        weight_fee = 0.0
        if weight_kg and weight_kg > 5:  # Free up to 5kg
            weight_fee = (weight_kg - 5) * 0.5  # $0.50 per kg over 5kg
        
        total_cost = base_cost + weight_fee
        
        return {
            "distance_km": round(distance_km, 2),
            "base_cost": round(base_cost, 2),
            "weight_fee": round(weight_fee, 2),
            "total_cost": round(total_cost, 2),
            "estimated_time_minutes": max(30, int(distance_km * 3))  # Rough estimate: 3 min per km, min 30 min
        }
