from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_menus():
    return [{"id": 1, "name": "Pasta", "price": 12000}]
