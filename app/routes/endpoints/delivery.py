from fastapi import APIRouter, Depends, Query
from app.services.delivery import DeliveryService

router = APIRouter()


@router.post("/estimate")
async def estimate_delivery(
    pickup_lat: float = Query(..., description="Pickup latitude", ge=-90, le=90),
    pickup_lng: float = Query(..., description="Pickup longitude", ge=-180, le=180),
    delivery_lat: float = Query(..., description="Delivery latitude", ge=-90, le=90),
    delivery_lng: float = Query(..., description="Delivery longitude", ge=-180, le=180),
    weight_kg: float = Query(None, description="Package weight in kg", ge=0)
):
    """Estimate delivery cost and time based on distance"""
    service = DeliveryService()
    
    estimate = service.estimate_delivery_cost_and_distance(
        pickup_lat, pickup_lng, delivery_lat, delivery_lng, weight_kg
    )
    
    return {
        "pickup_location": {"latitude": pickup_lat, "longitude": pickup_lng},
        "delivery_location": {"latitude": delivery_lat, "longitude": delivery_lng},
        "estimate": estimate
    }


@router.get("/{delivery_id}/status")
async def get_delivery_status(delivery_id: int):
    """Get delivery status (placeholder - will be implemented with order system)"""
    return {"message": f"Delivery status for ID {delivery_id} - to be implemented with order system"}
