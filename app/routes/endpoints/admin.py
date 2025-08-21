from fastapi import APIRouter

router = APIRouter()

@router.get("/merchants/pending")
async def pending_merchants():
    return {"message": "Pending merchants - to be implemented"}
