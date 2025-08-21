from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_reviews():
    return {"message": "List reviews - to be implemented"}
