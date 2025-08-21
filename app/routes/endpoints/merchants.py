from fastapi import APIRouter

router = APIRouter()

@router.post("/apply")
async def apply_merchant():
    return {"message": "Merchant application - to be implemented"}
