from fastapi import APIRouter
from app.routes import users, menus

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(menus.router, prefix="/menus", tags=["menus"])
